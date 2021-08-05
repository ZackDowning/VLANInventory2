# VLANInventory
Single-file executable to collect inventory of VLANs across a Cisco campus network.  
Adapted from [CommandRunner](https://github.com/ZackDowning/CommandRunner).

Outputs CSV file containing list of VLAN IDs and corresponding VLAN names.
## Requirements
- Windows Operating System to run executable on
- Text file with list of management IP addresses for devices
  - Example: example.txt
    ```
    1.1.1.1
    2.2.2.2
    3.3.3.3
    ```
- Administration credentials for devices
- ICMP ping reachability to management IP addresses of devices
- Device running Cisco IOS, IOS-XE, or NX-OS operating system
## Executable Windows
### File Selection
![alt text](https://i.imgur.com/qN7YBHC.png)
### Terminal
![alt text](https://i.imgur.com/4FJM0Yh.png)