import argparse
import requests
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
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

def upload_presets_to_device(device, presets_file):
    url = f"http://{device.parsed_addresses()[0]}:{device.port}/edit?save=presets.json"
    #curl -F "data=@presets.json" "http://[WLED-IP]/edit?save=presets.json"
    with open(presets_file, "rb") as file_data:
        # Send the POST request with multipart/form-data
        response = requests.post(url, files={"data": file_data})

        ##response = requests.post(url, json=presets, headers={'Content-Type': 'application/json'}, timeout=5)
        if response.status_code == 200:
            print(f"Successfully uploaded presets to {device.server}")
        else:
            print(f"Failed to upload presets to {device.server}: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="Configure WLED LED and hardware settings.")
    parser.add_argument("--target-ip", help="The IP address of the WLED device.")
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
    parser.add_argument("presets_file", help="Path to the presets.json file")
    args = parser.parse_args()

    if args.discover:
        devices = discover_wled_devices()
        if not devices:
            print("No WLED devices found.")
            exit(1)
        if len(devices) > 0:
            devices = select_wled_device(devices)
        for device in devices:
            target_ip = device.parsed_addresses()[0]
            upload_presets_to_device(device, args.presets_file)
    elif args.target_ip:
        upload_presets_to_device(args.target_ip, args.presets_file)
    else:
        print("Please provide either --target-ip or --discover option.")
        exit(1)

if __name__ == "__main__":
    main()