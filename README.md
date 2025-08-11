# WLED Configurator

A toolkit for configuring and managing WLED controllers from scratch, including network setup, configuration deployment, and preset management.

## 🚀 Quick Start

### Prerequisites

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

1. Ensure your WLED controllers are either:
   - In AP mode (broadcasting `WLED-AP` network)
   - Already connected to your network and discoverable via mDNS

## 📋 Complete Setup Process

### Step 1: Initial WLED Controller Configuration

Configure a fresh WLED controller with network settings and device name:

```bash
python wled-config.py --set-use-dhcp --set-ssid <WIFI_SSID> --set-password <WIFI_PASSWORD> --set-name <DEVICE_NAME> --discover
```

**Available Configuration Options:**

- `--set-ssid`: WiFi network SSID for the WLED device
- `--set-password`: WiFi network password  
- `--set-use-dhcp`: Enable DHCP (automatic IP assignment)
- `--set-ip-address`: Static IP address (alternative to DHCP)
- `--set-subnet-mask`: Subnet mask for static IP
- `--set-gateway`: Gateway address for static IP
- `--set-name`: Device name and mDNS hostname
- `--discover`: Use network discovery instead of AP mode connection
- `--wled-ap-ssid`: Override default WLED AP name (default: "WLED-AP")
- `--wled-ap-password`: Override default WLED AP password (default: "wled1234")

### Step 2: Deploy Complete Configuration

After initial setup, deploy full device configurations:

```bash
python push-config.py --config-file final-config.json --discover
```

Or target specific IP addresses:
```bash
python push-config.py --config-file final-config.json --target-ip 10.201.12.11,10.201.12.12
```

### Step 3: Load Presets

Deploy lighting presets to your configured controllers:

```bash
python push-presets.py --preset-file presets-collect.json --discover
```

Or for specific devices:
```bash
python push-presets.py --preset-file presets-collect.json --target-ip 10.201.12.11,10.201.12.12
```

## 🎨 Available Preset Collections

The project includes several preset collections for different scenarios:

| Preset File | Description | Use Case |
|-------------|-------------|----------|
| `presets-collect.json` | Collection effects | Standard lighting presets for collect |
| `presets-collect-dim.json` | Dimmed collection effects | Low-light environments |
| `presets-collect-green.json` | Green debug effects | Testing the deployment |
| `presets-stations.json` | Station-specific presets | Presets for stations |
| `presets-stations-dim.json` | Dimmed station presets | Low-light presets for stations |
| `presets-117.json` | Device-specific (WLED-117) | Individual device config |
| `presets-259-fire.json` | Fire effects for WLED-259 | Specialized fire preset |

## 🛠 Batch Operations

### Using Shell Scripts (Linux/macOS)

Quick deployment scripts are provided for common operations:

```bash
# Deploy collect presets to multiple controllers
./push-preset-collect.sh

# Deploy station presets
./push-preset-stations.sh

# Deploy dimmed versions
./push-preset-collect-dim.sh

# Deploy green-themed presets
./push-preset-collect-green.sh
```

### Using Batch Files (Windows)

```cmd
# Deploy collect presets
push-preset-collect.bat

# Deploy station presets  
push-preset-stations.bat

# Deploy configuration
push-config.bat
```

### Bulk Operations Script

For managing multiple controllers at once:

```bash
./run_batch.sh
```

## 📡 Device Management

### Device Discovery

The tools support automatic device discovery via mDNS:

```bash
# Discover all WLED devices on network
python wled-config.py --discover

# Interactive device selection
python push-presets.py --discover
```

### Device Inventory

The `wled.csv` file contains your device inventory with IP mappings:
```
WLED-101    10.201.12.11/24
WLED-234    10.201.12.12/24
WLED-235    10.201.12.13/24
...
```

### Rebooting Controllers

Reboot controllers after configuration changes:

```bash
python reboot.py --target-ip 10.201.12.11,10.201.12.12
```

Or discover and reboot all:

```bash
python reboot.py --discover
```

## 📁 Configuration Files

### Main Configuration (`final-config.json`)

Contains complete WLED configuration including:

- Network settings (WiFi, IP configuration)
- Device identification (name, mDNS)
- Hardware settings
- Default lighting parameters

### Preset Files Structure

Preset files use WLED's JSON format:

```json
{
    "0": {},  // Empty preset (off)
    "1": {    // Preset ID 1
        "playlist": {
            "ps": [4, 3],           // Preset sequence
            "dur": [10, 30],        // Duration per preset
            "transition": [0, 20],  // Transition times
            "repeat": 1,            // Repeat count
            "end": 2,              // End behavior
            "r": 0                 // Random
        }
    }
}
```

## 🔧 Troubleshooting

### Connection Issues

1. Verify WLED controller is powered and accessible
2. Check network connectivity to device IP
3. Ensure mDNS is working for discovery mode
4. Try connecting directly to WLED AP mode

### Configuration Deployment

1. Verify JSON syntax in configuration files
2. Check device compatibility with configuration
3. Monitor device logs for error messages
4. Reboot controller after major configuration changes

### Common Commands

```bash
# Test device connectivity
ping 10.201.12.11

# Check mDNS discovery
python -c "from wled_config import discover_wled_devices; print(discover_wled_devices())"

# Validate JSON configuration
python -m json.tool final-config.json
```

## 📚 Advanced Usage

### Custom Preset Development

1. Create preset using WLED web interface
2. Export configuration via WLED API or via the webpage under config > security & updates there is a backup presets option. It will create a file that you can then use to import them to another controller. 
3. Add to appropriate preset collection file
4. Deploy using push-presets.py

