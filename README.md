# wled-configurator

A small helper script to configure WLED device in an automated manner.

Usage:

    python wled-config.py --set-use-dhcp --set-ssid <SSID> --set-password <password> --set-name <device-name> --discover

Options:

    --set-ssid: set the SSID for the wled device to connect as a client.
    --set-password: set the SSID password for the wled device to connect as a client.
    --set-use-dhcp: configure dhcp
    --set-ip-address:  static ip to assign the wled device
    --set-subnet-mask: static subnet mask to assign the wled device
    --set-gateway: static gateway to assign the wled device
    --set-name: set name and mDNS name of thje device.
    --discover: use mDNS discovery instead of connecting to the AP-WIFI
    --wled-ap-ssid (optional, default="WLED-AP"): Override the default WLED-AP SSID.
    --wled-ap-password (optional, default="wled1234"): Password for the WLED-AP SSID.
    