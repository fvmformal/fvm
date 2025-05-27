def change_vhdl_line(file_path, line_number, new_content):
    """
    Changes the content of a specific line in a VHDL file.

    :param file_path: Path to the VHDL file.
    :param line_number: Line number to change (starts at 1).
    :param new_content: New content for that line.
    """
    # Read all lines from the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Check if the line exists
    if line_number <= 0 or line_number > len(lines):
        print("Line number out of range.")
        return
    
    # Change the content of the specific line
    lines[line_number - 1] = new_content + '\n'
    
    # Write the changes back to the file
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"Line {line_number} successfully changed.")

vhdl_file = 'PoC/src/net/ipv6/ipv6_Wrapper.vhdl'
line_number = 346
new_content = "	TX_StmMux_DestIPv6Address_Data <= TX_StmMux_Meta(15 downto 8);"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/ipv6/ipv6_Wrapper.vhdl'
line_number = 347
new_content = "	TX_StmMux_Length	<= TX_StmMux_Meta(31 downto 16);"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/ipv6/ipv6_Wrapper.vhdl'
line_number = 348
new_content = "	TX_StmMux_NextHeader <= TX_StmMux_Meta(39 downto 32);"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/common/my_config.vhdl.template'
line_number = 48
new_content = "	constant MY_BOARD: string	:= \"ML505\"; -- e.g. Custom, ML505, KC705, Atlys"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/common/my_config.vhdl.template'
line_number = 49
new_content = "	constant MY_DEVICE: string	:= \"EP2SGX90FF1508C3\"; -- e.g. None, XC5VLX50T-1FF1136, EP2SGX90FF1508C3"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/arith/arith_carrychain_inc.vhdl'
line_number = 60
new_content = "	genGeneric : if true generate"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/arith/arith_carrychain_inc.vhdl'
line_number = 67
new_content = "	genXilinx : if false generate"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/arith/arith_prefix_and.vhdl'
line_number = 57
new_content = "	genGeneric : if true generate"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/arith/arith_prefix_and.vhdl'
line_number = 73
new_content = "	genXilinx : if false generate"

change_vhdl_line(vhdl_file, line_number, new_content)


vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 269
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 543
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 544
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 545
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 550
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 551
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 552
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 553
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 554
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 555
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 556
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 557
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 558
new_content = ""

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 247
new_content = "	function to_net_mac_address_string(str : string)							return T_NET_MAC_ADDRESS;"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 786
new_content = "	function to_net_mac_address_string(str : string) return T_NET_MAC_ADDRESS is"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 795
new_content = "	constant C_NET_MAC_SOURCEFILTER_NONE	: T_NET_MAC_INTERFACE	:= (Address => to_net_mac_address_string(\"00:00:00:00:00:01\"), Mask => C_NET_MAC_MASK_EMPTY);"

change_vhdl_line(vhdl_file, line_number, new_content)

vhdl_file = 'PoC/src/net/net.pkg.vhdl'
line_number = 804
new_content = "constant C_NET_MAC_ETHERNETTYPE_SSFC						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"A987\"); 	constant C_NET_MAC_ETHERNETTYPE_SWAP						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"FFFE\");	constant C_NET_MAC_ETHERNETTYPE_LOOPBACK				: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"FFFF\");	constant C_NET_MAC_ETHERNETTYPE_IPV4						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"0800\");	constant C_NET_MAC_ETHERNETTYPE_ARP							: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"0806\");	constant C_NET_MAC_ETHERNETTYPE_WOL							: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"0842\");	constant C_NET_MAC_ETHERNETTYPE_VLAN						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"8100\");	constant C_NET_MAC_ETHERNETTYPE_SNMP						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"814C\");	constant C_NET_MAC_ETHERNETTYPE_IPV6						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"86DD\");	constant C_NET_MAC_ETHERNETTYPE_MACCONTROL			: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"8808\");	constant C_NET_MAC_ETHERNETTYPE_JUMBOFRAMES			: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"8870\");	constant C_NET_MAC_ETHERNETTYPE_QINQ						: T_NET_MAC_ETHERNETTYPE		:= to_net_mac_ethernettype(x\"9100\");"

change_vhdl_line(vhdl_file, line_number, new_content)