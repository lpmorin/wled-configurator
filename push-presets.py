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

def upload_presets_to_device(device, presets_file):
    url = f"http://{device.server}:{device.port}/edit?save=presets.json"
    
    try:
        print(f"Attempting to upload presets to {device.server}...")
        
        # Check if the presets file exists before trying to open it
        with open(presets_file, "rb") as file_data:
            # Send the POST request with multipart/form-data and timeout
            response = requests.post(url, files={"data": file_data}, timeout=10)

            if response.status_code == 200:
                print(f"✓ Successfully uploaded presets to {device.server}")
                return True
            else:
                print(f"✗ Failed to upload presets to {device.server}: HTTP {response.status_code}")
                return False
                
    except requests.exceptions.Timeout:
        print(f"✗ Timeout error connecting to {device.server} (device may be offline or slow)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection error to {device.server} (device may be offline or unreachable)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error to {device.server}: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Error: Presets file '{presets_file}' not found")
        return False
    except Exception as e:
        print(f"✗ Unexpected error uploading to {device.server}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Configure WLED LED and hardware settings.")
    parser.add_argument('--target-ip', type=str, help='Comma separated list of target IPs (ex: 192.168.1.10,192.168.1.11)')
    parser.add_argument("--discover", action="store_true", help="Use mDNS discovery to find WLED devices.")
    parser.add_argument("presets_file", help="Path to the presets.json file")
    args = parser.parse_args()

    successful_uploads = 0
    failed_uploads = 0

    if args.discover:
        devices = discover_wled_devices()
        if not devices:
            print("No WLED devices found.")
            exit(1)
        if len(devices) > 0:
            devices = select_wled_device(devices)
        
        print(f"\nUploading presets to {len(devices)} device(s)...")
        for device in devices:
            device.server = device.parsed_addresses()[0]
            device.port = device.port
            if upload_presets_to_device(device, args.presets_file):
                successful_uploads += 1
            else:
                failed_uploads += 1
                
    elif args.target_ip:
        # Handle multiple IPs entered as comma separated string
        target_ips = [ip.strip() for ip in args.target_ip.split(',')]
        print(f"Using target IP(s): {target_ips}")
        print(f"\nUploading presets to {len(target_ips)} device(s)...")
        
        # For each IP provided, you can perform your operation.
        # Example: push presets to each target IP.
        for ip in target_ips:
            device = WLEDDevice(ip=ip)
            if upload_presets_to_device(device, args.presets_file):
                successful_uploads += 1
            else:
                failed_uploads += 1

    else:
        print("Please provide either --target-ip or --discover option.")
        exit(1)

    # Print summary
    total_devices = successful_uploads + failed_uploads
    print(f"\n{'='*50}")
    print(f"Upload Summary:")
    print(f"  Total devices: {total_devices}")
    print(f"  Successful: {successful_uploads}")
    print(f"  Failed: {failed_uploads}")
    
    if failed_uploads > 0:
        print(f"  Success rate: {(successful_uploads/total_devices)*100:.1f}%")
        exit(1)  # Exit with error code if any uploads failed
    else:
        print(f"  All uploads completed successfully!")
        exit(0)

if __name__ == "__main__":
    main()