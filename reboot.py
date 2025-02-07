import argparse
import requests
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

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
        print("\nAvailable WLED controllers:")
        for i, device in enumerate(devices):
            print(f"{i + 1}: {device.name} - {device.parsed_addresses()[0]}")
        selection = input("Select one or more controllers (comma-separated, 'a' for all, 'r' to refresh, 'q' to quit): ")
        
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

def send_reboot_command(target_ip):
    try:
        print(f"Sending reboot command to {target_ip}...")
        restart_command = json.dumps({"rb": True})
        response = requests.post(f"http://{target_ip}/json/state", data=restart_command, headers={'Content-Type': 'application/json'}, timeout=5)
        print(f"Reboot command sent to {target_ip}.")
    except requests.exceptions.ReadTimeout:
        print(f"Reboot command sent to {target_ip}. Device will reboot in a few seconds.")
    except requests.RequestException as e:
        print(f"Failed to send reboot command to {target_ip}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Send reboot command to WLED devices.")
    parser.add_argument("--target-ip", help="Comma separated IP addresses of the WLED devices.")
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
    args = parser.parse_args()

    if args.target_ip:
        # Split and strip the IPs so we have a list
        target_ips = [ip.strip() for ip in args.target_ip.split(',')]
    else:
        target_ips = []

    if args.discover:

        devices = discover_wled_devices()
        if not devices:
            print("No WLED devices found.")
            exit(1)
        if len(devices) > 0:
            devices = select_wled_device(devices)
            target_ips.extend(device.parsed_addresses()[0] for device in devices)
    if not target_ips:
        print("Please provide at least one target IP address or use mDNS discovery.")
        return

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(send_reboot_command, ip) for ip in target_ips]
        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()