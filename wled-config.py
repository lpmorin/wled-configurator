import subprocess
import time
import requests
import argparse
import platform
import csv
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener

class WLEDListener(ServiceListener):
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            self.devices.append(info)

def discover_wled_devices():
    zeroconf = Zeroconf()
    listener = WLEDListener()
    browser = ServiceBrowser(zeroconf, "_wled._tcp.local.", listener)
    time.sleep(5)  # Wait for discovery
    zeroconf.close()
    return listener.devices

def select_wled_device(devices):
    while True:
        print("Multiple WLED controllers found:")
        for i, device in enumerate(devices):
            print(f"{i + 1}: {device.name} - {device.parsed_addresses()[0]}")
        selection = input("Select one or more controllers (comma-separated, 'a' for all, 'r' to refresh, or 'q' to quit): ")
        
        if selection.lower() == 'q':
            print("Quitting the program.")
            exit(0)
        elif selection.lower() == 'r':
            print("Refreshing device list...")
            devices = discover_wled_devices()
            if not devices:
                print("No WLED devices found.")
                exit(1)
        elif selection.lower() == 'a':
            return devices
        else:
            try:
                indices = [int(x) - 1 for x in selection.split(',')]
                return [devices[i] for i in indices]
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")

def connect_to_wifi(ssid, password, system_os):
    if system_os == "Windows":
        # Windows command to connect to a Wi-Fi network
        if password:
            command = f'netsh wlan connect name="{ssid}" ssid="{ssid}" key="{password}"'
        else:
            command = f'netsh wlan connect name="{ssid}" ssid="{ssid}"'
        subprocess.run(command, shell=True)
    
    elif system_os == "Linux":
        # Linux command to connect to a Wi-Fi network using nmcli
        if password:
            command = f'nmcli dev wifi connect "{ssid}" password "{password}"'
        else:
            command = f'nmcli dev wifi connect "{ssid}"'
        subprocess.run(command, shell=True)

    elif system_os == "Darwin":  # macOS
        # macOS command to connect to a Wi-Fi network using networksetup
        network_interface = "Wi-Fi"  # Default Wi-Fi interface name on macOS; adjust if different
        if password:
            command = f'networksetup -setairportnetwork {network_interface} "{ssid}" "{password}"'
        else:
            command = f'networksetup -setairportnetwork {network_interface} "{ssid}"'
        subprocess.run(command, shell=True)

    else:
        print(f"Unsupported OS: {system_os}")
        return False
    
    time.sleep(5)  # Wait for the connection to establish
    return True

def log_to_csv(logfile, name, ip_address, mac_address):
    with open(logfile, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([name, ip_address, mac_address])

def configure_wled(target_ip,
                   set_ssid, 
                   set_password, 
                   set_use_dhcp, 
                   set_ip_address=None, 
                   set_subnet_mask=None, 
                   set_gateway=None,
                   set_name=None,
                   logfile=None
                    ):
    # Convert IP, gateway, and subnet mask to list of integers
    def ip_to_list(ip):
        return [int(x) for x in ip.split('.')]
    
    # Generate mDNS based on the name
    mdns = set_name.lower().replace(' ', '-') if set_name else None
    
    # Step 2: Send the configuration payload to WLED
    payload = {
        "id": {
            "mdns": mdns,
            "name": set_name,
            "inv": "Light"
        },
        "nw": {
            "ins": [
                {
                    "ssid": set_ssid,
                    "pskl": len(set_password),
                    "psk": set_password,
                    "ip": ip_to_list(set_ip_address) if set_ip_address else [0, 0, 0, 0],
                    "gw": ip_to_list(set_gateway) if set_gateway else [0, 0, 0, 0],
                    "sn": ip_to_list(set_subnet_mask) if set_subnet_mask else [0, 0, 0, 0]
                }
            ]
        },
        "ap": {
            "ssid": "WLED-AP",
            "pskl": 8,
            "chan": 1,
            "hide": 0,
            "behav": 0,
            "ip": [4, 3, 2, 1]
        },
        "wifi": {
            "sleep": True
        }
    }

    if not set_use_dhcp and (not set_ip_address or not set_subnet_mask or not set_gateway):
        print("Static IP configuration requires IP address, subnet mask, and gateway.")
        return

    try:
        # Retrieve and print the MAC address
        response = requests.get(f"http://{target_ip}/json/info", timeout=5)
        response.raise_for_status()
        mac_address = response.json().get("mac", "Unknown MAC address")
        print(f"Configuring device MAC address: {mac_address}")
        
        print("Sending configuration to WLED...")
        response = requests.post(f"http://{target_ip}/json/cfg", json=payload, timeout=5)
        response.raise_for_status()
        print("Configuration sent successfully.")
        
        # Log to CSV
        if logfile:
            log_to_csv(logfile, set_name, set_ip_address, mac_address)
        
    except requests.RequestException as e:
        print(f"Failed to send configuration: {e}")

def read_csv_file(csv_file):
    entries = []
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                entries.append((row[0], row[1]))
    return entries

def main():
    parser = argparse.ArgumentParser(description="Configure WLED with new Wi-Fi settings.")
    parser.add_argument("--target-ip", default="4.3.2.1", help="The IP address of the WLED device.")
    parser.add_argument("--wled-ap-ssid", default="WLED-AP", help="Override the default WLED-AP SSID.")
    parser.add_argument("--wled-ap-password", default="wled1234", help="Password for the WLED-AP SSID.")
    parser.add_argument("--set-ssid", help="The SSID of the target Wi-Fi network.", required=True)
    parser.add_argument("--set-password", help="The password of the target Wi-Fi network.", required=True)
    parser.add_argument("--set-use-dhcp", action="store_true", help="Use DHCP for IP configuration.")
    parser.add_argument("--set-ip-address", help="Static IP address for the WLED device.")
    parser.add_argument("--set-subnet-mask", help="Subnet mask for the static IP configuration.")
    parser.add_argument("--set-gateway", help="Gateway for the static IP configuration.")
    parser.add_argument("--set-name", help="The name of the WLED device.", required=False)
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
    parser.add_argument("--logfile", help="Path to the CSV logfile.")
    parser.add_argument("--csv-file", help="Path to the input CSV file containing name and IP address.")
    args = parser.parse_args()

    system_os = platform.system()
    WLED_AP_SSID = args.wled_ap_ssid
    WLED_AP_PASS = args.wled_ap_password

    if args.csv_file:
        entries = read_csv_file(args.csv_file)
        for name, ip_address in entries:
            connect_to_wifi(WLED_AP_SSID, WLED_AP_PASS, system_os)
            configure_wled(
                target_ip=args.target_ip,
                set_ssid=args.set_ssid,
                set_password=args.set_password,
                set_use_dhcp=args.set_use_dhcp,
                set_ip_address=ip_address,
                set_subnet_mask=args.set_subnet_mask,
                set_gateway=args.set_gateway,
                set_name=name,
                logfile=args.logfile
            )
            input(f"Configuration for {name} ({ip_address}) completed. Press any key to continue...")
    elif args.discover:
        devices = discover_wled_devices()
        if not devices:
            print("No WLED devices found.")
            exit(1)
        if len(devices) > 0:
            devices = select_wled_device(devices)
        for device in devices:
            target_ip = device.parsed_addresses()[0]
            connect_to_wifi(WLED_AP_SSID, WLED_AP_PASS, system_os)
            configure_wled(
                target_ip=target_ip,
                set_ssid=args.set_ssid,
                set_password=args.set_password,
                set_use_dhcp=args.set_use_dhcp,
                set_ip_address=args.set_ip_address,
                set_subnet_mask=args.set_subnet_mask,
                set_gateway=args.set_gateway,
                set_name=args.set_name,
                logfile=args.logfile
            )
    else:
        connect_to_wifi(WLED_AP_SSID, WLED_AP_PASS, system_os)
        configure_wled(
            target_ip=args.target_ip,
            set_ssid=args.set_ssid,
            set_password=args.set_password,
            set_use_dhcp=args.set_use_dhcp,
            set_ip_address=args.set_ip_address,
            set_subnet_mask=args.set_subnet_mask,
            set_gateway=args.set_gateway,
            set_name=args.set_name,
            logfile=args.logfile
        )

if __name__ == "__main__":
    main()
