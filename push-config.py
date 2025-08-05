import argparse
import requests
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import time
import json

class WLEDDevice:
    def __init__(self, ip, port=80):
        self.server = ip
        self.port = port

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

def configure_wled_hardware(device):
    """Configure WLED hardware settings with robust error handling."""
    target_ip = device.server if hasattr(device, 'server') else device
    
    try:
        print(f"Attempting to configure device at {target_ip}...")
        
        # Get current device info
        print("  → Getting device information...")
        response = requests.get(f"http://{target_ip}/json/info", timeout=10)
        response.raise_for_status()
        mac_address = response.json().get("mac", "Unknown MAC address")
        device_name = response.json().get("name", "Unknown device")
        print(f"  → Found device: {device_name} (MAC: {mac_address})")

        # Send LED configuration
        print("  → Sending LED configuration...")
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
        
        response = requests.post(f"http://{target_ip}/json/cfg", 
                               data=json.dumps(led_config), 
                               headers={'Content-Type': 'application/json'}, 
                               timeout=10)
        response.raise_for_status()
        print("  → Configuration sent successfully")

        # Verify the settings were applied
        print("  → Verifying configuration...")
        response = requests.get(f"http://{target_ip}/json/cfg", timeout=10)
        response.raise_for_status()
        current_config = response.json()
        
        # Check if LED count was applied correctly
        led_total = current_config.get("hw", {}).get("led", {}).get("total", 0)
        if led_total == 24:
            print(f"  → Configuration verified: LED count = {led_total}")
        else:
            print(f"  → Warning: Expected 24 LEDs, but device shows {led_total}")
        
        # Restart WLED using the JSON API
        print("  → Restarting WLED...")
        restart_command = json.dumps({"rb": True})
        response = requests.post(f"http://{target_ip}/json/state", 
                               data=restart_command, 
                               headers={'Content-Type': 'application/json'}, 
                               timeout=5)
        response.raise_for_status()
        print("  → Restart command sent successfully")
        print(f"✓ Successfully configured {target_ip} - device will reboot")
        return True
        
    except requests.exceptions.Timeout:
        print(f"✗ Timeout error connecting to {target_ip} (device may be offline or slow)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection error to {target_ip} (device may be offline or unreachable)")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error from {target_ip}: {e.response.status_code} - {e.response.reason}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error to {target_ip}: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON response from {target_ip}: {e}")
        return False
    except KeyError as e:
        print(f"✗ Missing expected data in response from {target_ip}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error configuring {target_ip}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Configure WLED LED and hardware settings.")
    parser.add_argument('--target-ip', type=str, help='Comma separated list of target IPs (ex: 192.168.1.10,192.168.1.11)')
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
    args = parser.parse_args()

    successful_configs = 0
    failed_configs = 0

    if args.discover:
        devices = discover_wled_devices()
        if not devices:
            print("No WLED devices found.")
            exit(1)
        if len(devices) > 0:
            devices = select_wled_device(devices)
        
        print(f"\nConfiguring {len(devices)} device(s)...")
        for device in devices:
            target_ip = device.parsed_addresses()[0]
            device_obj = WLEDDevice(target_ip)
            if configure_wled_hardware(device_obj):
                successful_configs += 1
            else:
                failed_configs += 1
                
    elif args.target_ip:
        # Handle multiple IPs entered as comma separated string
        target_ips = [ip.strip() for ip in args.target_ip.split(',')]
        print(f"Using target IP(s): {target_ips}")
        print(f"\nConfiguring {len(target_ips)} device(s)...")
        
        for ip in target_ips:
            device = WLEDDevice(ip)
            if configure_wled_hardware(device):
                successful_configs += 1
            else:
                failed_configs += 1
                
    else:
        print("Please provide either --target-ip or --discover option.")
        exit(1)

    # Print summary
    total_devices = successful_configs + failed_configs
    print(f"\n{'='*50}")
    print(f"Configuration Summary:")
    print(f"  Total devices: {total_devices}")
    print(f"  Successful: {successful_configs}")
    print(f"  Failed: {failed_configs}")
    
    if failed_configs > 0:
        print(f"  Success rate: {(successful_configs/total_devices)*100:.1f}%")
        print("\nNote: Failed devices may be offline, unreachable, or running incompatible firmware.")
        exit(1)  # Exit with error code if any configurations failed
    else:
        print(f"  All configurations completed successfully!")
        print("\nDevices are rebooting and should be available shortly.")
        exit(0)

if __name__ == "__main__":
    main()