#!/usr/bin/env python3

"""
Konfigurasjonsskript for Cisco 2960-switcher ved hjelp av Netmiko.

Dette skriptet:
- Ber bruker om antall switcher som skal konfigureres
- Ber om start-VLAN for elevporter
- Ber om antall elevporter (access-porter)
- Ber om antall trunk-porter
- Oppretter VLAN (fra start-VLAN, fortløpende) for elevporter
- Konfigurerer VLAN 10 som management-VLAN
- Setter port security på access-porter (en enkel port security)
- Konfigurerer trunkporter (native VLAN 10 og tillater alle VLAN)
- Tildeler IP-adresse på VLAN 10 (statisk eksempel, men kan utvides)
"""

from netmiko import ConnectHandler

def generate_switch_config(
    hostname: str,
    ip_address: str,
    username: str,
    password: str,
    start_vlan: int,
    num_elev_ports: int,
    num_trunk_ports: int
):
    """
    Genererer en liste med konfigurasjonslinjer for én switch.
    Returnerer en liste med kommandoer som skal sendes til switchen.
    """

    # VLAN 10 = "Management VLAN"
    # For enkelhetens skyld legger vi IP-adresse 10.0.10.X/24 (X = id for switch)
    # men man kan endre dette til f.eks. 10.0.10.2/24 eller DHCP etc.

    config_cmds = []

    # 1. Gi switch et hostname
    config_cmds.append(f"hostname {hostname}")

    # 2. Konfigurer VLAN 10 som Management
    config_cmds.extend([
        "ip routing",  # Hvis man ønsker at switch skal kunne route VLAN internt (valgfritt)
        "no ip domain-lookup"
    ])
    config_cmds.append("interface vlan 10")
    config_cmds.append(f"ip address {ip_address} 255.255.255.0")
    config_cmds.append("no shutdown")

    # 3. Opprett VLAN for elevporter
    #    F.eks. hvis start_vlan = 11 og num_elev_ports = 20, 
    #    tildeler vi VLAN 11 til port 1, VLAN 12 til port 2 osv.
    for i in range(num_elev_ports):
        vlan_id = start_vlan + i
        config_cmds.append(f"vlan {vlan_id}")
        config_cmds.append(f" name elev{vlan_id}")
        config_cmds.append("exit")  # gå ut av vlan-konfig

    # 4. Konfigurer access-porter
    #    Anta at portene starter på 1 og går til num_elev_ports
    #    VLAN tildeles løpende
    for i in range(num_elev_ports):
        vlan_id = start_vlan + i
        interface_id = i + 1  # portnummer, starts from 1
        config_cmds.append(f"interface GigabitEthernet0/{interface_id}")
        config_cmds.append("switchport mode access")
        config_cmds.append(f"switchport access vlan {vlan_id}")
        # Enkel port security
        config_cmds.append("switchport port-security")
        config_cmds.append("switchport port-security maximum 2")
        config_cmds.append("switchport port-security violation restrict")
        config_cmds.append("spanning-tree portfast")
        config_cmds.append("exit")

    # 5. Konfigurer trunkporter
    #    Anta at trunk-portene følger rett etter elevportene.
    #    Hvis num_elev_ports = 20, da trunk-porter = 21–26 i eksempelet.
    start_trunk_port = num_elev_ports + 1
    for j in range(num_trunk_ports):
        interface_id = start_trunk_port + j
        config_cmds.append(f"interface GigabitEthernet0/{interface_id}")
        config_cmds.append("switchport mode trunk")
        config_cmds.append("switchport trunk encapsulation dot1q")  # 2960 støtter normalt kun dot1q
        config_cmds.append("switchport trunk native vlan 10")
        config_cmds.append("switchport trunk allowed vlan all")
        config_cmds.append("exit")

    # 6. Lagre konfigurasjon
    config_cmds.append("end")
    config_cmds.append("write memory")

    return config_cmds


def main():
    print("=== Cisco 2960 konfigurasjonsskript ===")

    username = input("Tast inn brukernavn for switch-tilkobling: ")
    password = input("Tast inn passord for switch-tilkobling: ")

    # Hvor mange switcher skal konfigureres?
    antall_switcher = int(input("Hvor mange switcher skal konfigureres? (f.eks. 3): "))

    # Hvilket VLAN skal vi starte med for elevporter?
    start_vlan = int(input("Start-VLAN for elevporter? (f.eks. 11): "))

    # Hvor mange porter skal være elevporter (access)?
    num_elev_ports = int(input("Antall elevporter? (f.eks. 20): "))

    # Hvor mange porter skal være trunk-porter?
    num_trunk_ports = int(input("Antall trunk-porter? (f.eks. 6): "))

    # Vi går gjennom hver switch
    for i in range(1, antall_switcher + 1):
        # Eksempel: definere IP-adresse til VLAN 10 pr. switch
        # Helt enkel logikk -> 10.0.10.(1 + i)
        ip_address = f"10.0.10.{i+1}"
        hostname = f"SW{i}"

        # IP-adresse for tilkobling (kan være management IP, SSH IP etc.)
        # For test kan du la dem være identiske med VLAN 10, men i praksis 
        # må du vite eksisterende mgmt-adresse, eller en console-tilkobling via IP.
        device_ip = input(f"Tast inn mgmt-IP for switch {i} (hostname: {hostname}): ")

        # Opprett netmiko dictionary
        device = {
            "device_type": "cisco_ios",
            "host": device_ip,
            "username": username,
            "password": password,
            "secret": password,  # enable secret hvis det er samme
            "port": 22,
        }

        # Koble til og kjør konfig
        try:
            print(f"\nKobler til {hostname} på {device_ip}...")
            net_connect = ConnectHandler(**device)
            net_connect.enable()

            # Generer konfigurasjonskommandoer
            cmds = generate_switch_config(
                hostname=hostname,
                ip_address=ip_address,
                username=username,
                password=password,
                start_vlan=start_vlan,
                num_elev_ports=num_elev_ports,
                num_trunk_ports=num_trunk_ports
            )

            print(f"Sender konfig til {hostname}...")
            output = net_connect.send_config_set(cmds)
            print(output)

            print(f"Ferdig konfig for {hostname}.\n")

            net_connect.disconnect()

        except Exception as e:
            print(f"Feil ved tilkobling/konfigurasjon på {hostname}: {e}")


if __name__ == "__main__":
    main()
