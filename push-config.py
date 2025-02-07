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

def configure_wled_hardware(target_ip):
    # LED and button configuration
    # LED and button configuration with Python booleans
    try:
        # Get current device info
        response = requests.get(f"http://{target_ip}/json/info", timeout=5)
        response.raise_for_status()
        mac_address = response.json().get("mac", "Unknown MAC address")
        print(f"\nConfiguring device MAC address: {mac_address}")

        # Send LED configuration
        print("Sending LED configuration...")
        led_config = {
            "hw": {
                "led": {
                    "total": 24,
                    "maxpwr": 250,
                    "ledma": 25,
                    "cct": False,
                    "cr": False,
                    "cb": 0,
                    "fps": 42,
                    "rgbwm": 255,
                    "ld": False,
                    "ins": [
                        {
                            "start": 0,
                            "len": 24,
                            "pin": [1],
                            "order": 0,
                            "rev": False,
                            "skip": 0,
                            "type": 22,
                            "ref": False,
                            "rgbwm": 0,
                            "freq": 0
                        }
                    ]
                },
                "btn": {
                    "max": 2,
                    "pull": True,
                    "ins": [
                        {
                            "type": 2,
                            "pin": [2],
                            "macros": [1, 2, 3]
                        },
                        {
                            "type": 0,
                            "pin": [-1],
                            "macros": [0, 0, 0]
                        }
                    ],
                    "tt": 32,
                    "mqtt": False
                }
            },
            "def": {
                "ps": 2,
                "on": True,
                "bri": 32
            }
        }
        response = requests.post(f"http://{target_ip}/json/cfg", data=json.dumps(led_config), headers={'Content-Type': 'application/json'}, timeout=5)
        response.raise_for_status()
        print("Configuration response:", response.text)

        # Let's also try to verify the settings were applied
        print("\nVerifying current configuration...")
        response = requests.get(f"http://{target_ip}/json/cfg", timeout=5)
        current_config = response.json()
        print("Current configuration:")
        print(json.dumps(current_config, indent=2))
        
        # Restart WLED using the JSON API
        print("\nRestarting WLED...")
        # Using json.dumps to convert Python True to JSON true
        restart_command = json.dumps({"rb": True})
        response = requests.post(f"http://{target_ip}/json/state", data=restart_command, headers={'Content-Type': 'application/json'}, timeout=2)
        restart_response = response.json()
        print("Restart command sent. Response from WLED:")
        print(json.dumps(restart_response, indent=2))
        print("\nDevice will reboot in a few seconds.")
        
    except requests.RequestException as e:
        print(f"Failed to send configuration: {e}")

def main():
    parser = argparse.ArgumentParser(description="Configure WLED LED and hardware settings.")
    parser.add_argument("--target-ip", help="The IP address of the WLED device.")
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
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
            configure_wled_hardware(target_ip)
    elif args.target_ip:
        configure_wled_hardware(args.target_ip)
    else:
        print("Please provide either --target-ip or --discover option.")
        exit(1)

if __name__ == "__main__":
    main()