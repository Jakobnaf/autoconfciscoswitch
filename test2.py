import argparse

def configure_switch(switch_id, start_vlan, num_elev_ports, num_trunk_ports):
    config = []
    
    # Konfigurer elevporter
    for port in range(1, num_elev_ports + 1):
        vlan_id = start_vlan + port - 1
        config.append(f"interface gi1/0/{port}")
        config.append(f" switchport mode access")
        config.append(f" switchport access vlan {vlan_id}")
        config.append(f" description elev{vlan_id}")

    # Konfigurer trunk-porter
    for port in range(num_elev_ports + 1, num_elev_ports + num_trunk_ports + 1):
        config.append(f"interface gi1/0/{port}")
        config.append(" switchport mode trunk")
        config.append(" switchport trunk native vlan 10")
        for vlan in range(start_vlan, start_vlan + num_elev_ports):
            config.append(f" switchport trunk allowed vlan add {vlan}")

    # Konfigurer VLAN 10 med IP-adresse og sikkerhet
    config.append("vlan 10")
    config.append(" name Management")
    config.append("!")
    config.append("interface vlan 10")
    config.append(" ip address 192.168.10.1 255.255.255.0")
    config.append(" ip access-group 10 in")
    config.append("!")
    config.append("access-list 10 permit ip any host 192.168.10.1")
    config.append("access-list 10 deny ip any any")

    return "\n".join(config)

def main():
    parser = argparse.ArgumentParser(description="Switch configuration script")
    parser.add_argument('--switches', type=int, default=3, help='Number of switches to configure')
    parser.add_argument('--start_vlan', type=int, default=11, help='Starting VLAN number')
    parser.add_argument('--num_elev_ports', type=int, default=20, help='Number of student ports')
    parser.add_argument('--num_trunk_ports', type=int, default=6, help='Number of trunk ports')
    
    args = parser.parse_args()

    for i in range(args.switches):
        print(f"Switch {i+1} Configuration:")
        print(configure_switch(i+1, args.start_vlan, args.num_elev_ports, args.num_trunk_ports))
        print("\n")

if __name__ == "__main__":
    main()