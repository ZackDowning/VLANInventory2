> **Archived: not maintained since 2021.** This repository is read-only and kept for reference. It is not reviewed or fixed any more. Known issues, left as they are:
> - With a failed SSH login the tool tries the same login again over Telnet (clear text), and SSH host keys are not checked.
> - Text from devices goes into the CSV report unfiltered, so a crafted device name can run as a formula when the report is opened.
> - The prebuilt Windows program was removed from this repository: it dated from 2021, did not match the source and was unsigned.
>
> Run it only on networks you own, and never with an administrator login you cannot change afterwards.

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

## Third-party templates

The parser templates in `templates/` are copied unchanged from [ntc-templates](https://github.com/networktocode/ntc-templates) (Copyright 2015 Jason Edelman, Network to Code, LLC), which is licensed under the Apache License 2.0. Its licence text is in `LICENSE-ntc-templates`. The rest of this repository is under the MIT licence in `LICENSE`.
