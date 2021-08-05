from gui import ManagementFileBrowseWindow
from general import Connection, MultiThread, Connectivity
from getpass import getpass
import re
import time


# PyInstaller bundle command:
# pyinstaller -F --hidden-import PySimpleGUI --add-data templates;templates main.py

# TODO: Add sorting algorithm function for output_vlans
# TODO: Add option to search for switches that have certain VLANs and output to seperate sheets in csv file
# TODO:     A) Collect inventory for all VLANS
# TODO:     B) Collect switch inventory that contain specific VLANs
# TODO:     Select from the following options: [A]/B


# Outputs failed device list to CSV file with columns:
# 'ip_address,connectivity,authentication,authorization,con_type,con_exception'
def output_failed_to_file(failed_list):
    with open('failed_devices.csv', 'w+') as file:
        file.write(
            'ip_address,connectivity,authentication,authorization,con_exception\n'
        )
        for device in failed_list:
            ip_address = device['ip']
            connectivity = device['connectivity']
            authentication = device['authentication']
            authorization = device['authorization']
            exception = device['exception']
            file.write(
                f'{ip_address},{connectivity},{authentication},{authorization},{exception}\n'
            )


def output_vlans(vlan_list):
    with open('vlans.csv', 'w+') as file:
        file.write(
            'vlan_id,name\n'
        )
        for vlan in vlan_list:
            vlan_id = vlan['vlan_id']
            name = vlan['name']
            file.write(
                f'{vlan_id},{name}\n'
            )


def output_switches(sw_vlan_inv):
    with open('sw_vlans.csv', 'w+') as file:
        file.write(
            'Switch Hostname,Switch IP Address,Connection Type,Device Type,VLAN ID,VLAN Name,# Active Intfs\n'
        )
        for sw in sw_vlan_inv:
            hostname = sw['hostname']
            ip_address = sw['ip_address']
            con_type = sw['con_type']
            device_type = sw['device_type']
            vlan_id = sw['vlan_id']
            vlan_name = sw['vlan_name']
            active_interfaces = sw['active_interfaces']
            file.write(
                f'{hostname},{ip_address},{con_type},{device_type},{vlan_id},{vlan_name},{active_interfaces}\n'
            )


class VlanInventory:
    def __init__(self):
        banner = 'VLANInventory'

        def vlan_inventory(device):
            cmd = 'show vlan brief'
            ip_address = device['ip']
            hostname = device['hostname']
            device_type = device['device_type']
            enable = device['enable']
            with Connection(ip_address, self.username, self.password, device_type, enable, self.enable_pw
                            ).connection().session as session:
                raw_show_vlan = session.send_command(cmd, use_textfsm=True, delay_factor=4)
                try:
                    for vlan in raw_show_vlan:
                        vlan_id = vlan['vlan_id']
                        if all(vlan_id != vid for vid in vlan_master['all_vlans']):
                            vlan_master['all_vlans'].append(vlan_id)
                            vlan_master['vlan_db'].append(
                                {
                                    'vlan_id': vlan_id,
                                    'name': vlan['name']
                                }
                            )
                except TypeError:
                    pass
            print(f'Done: {ip_address} - {hostname}')
            self.finished_devices.append(ip_address)

        def sw_vl_inventory(device):
            cmd = 'show vlan brief'
            ip_address = device['ip']
            hostname = device['hostname']
            device_type = device['device_type']
            enable = device['enable']
            con_type = device['con_type']
            with Connection(ip_address, self.username, self.password, device_type, enable, self.enable_pw
                            ).connection().session as session:
                raw_show_vlan = session.send_command(cmd, use_textfsm=True, delay_factor=4)
                try:
                    for vlan in raw_show_vlan:
                        interfaces = vlan['interfaces']
                        vlan_id = vlan['vlan_id']
                        vlan_name = vlan['name']
                        if any(vlan_id == vid for vid in vlans_to_check):
                            switch_vlan_inventory.append(
                                {
                                    'hostname': hostname,
                                    'ip_address': ip_address,
                                    'con_type': con_type,
                                    'device_type': device_type,
                                    'vlan_id': vlan_id,
                                    'vlan_name': vlan_name,
                                    'active_interfaces': str(len(interfaces))
                                }
                            )
                except TypeError:
                    pass
            print(f'Done: {ip_address} - {hostname}')
            self.finished_devices.append(ip_address)

        vlan_master = {
            'all_vlans': [],
            'vlan_db': []
        }

        switch_vlan_inventory = []

        self.mgmt_ips = ManagementFileBrowseWindow().mgmt_ips
        print(banner)
        try:
            if len(self.mgmt_ips) == 0:
                print('No IP addresses found in file provided.')
                input('Press Enter to close.')
        except TypeError:
            print('No file provided.')
            input('Press Enter to close.')
        else:
            while True:
                sw_vl_inventory_option = input('A) Collect inventory for all VLANS\n'
                                               'B) Collect switch inventory that contain specific VLANs\n'
                                               'Select from the following options: [A]/B: ')
                if re.fullmatch(r'[Aa]|', sw_vl_inventory_option):
                    sw_vl_inventory_option = False
                    break
                elif re.fullmatch(r'[Bb]', sw_vl_inventory_option):
                    sw_vl_inventory_option = True
                    break
                else:
                    continue

            if sw_vl_inventory_option:
                vlans_to_check = input('Enter VLANs seperating each with a comma and no space.\n'
                                       'Example: 100,200,300\n'
                                       'VLANs: ').split(',')

            self.username = input('Enter Username: ')
            self.password = getpass('Enter Password: ')
            self.enable_pw = getpass('(If applicable) Enter Enable Password: ')
            print('Testing connectivity, authentication, and authorization on devices...')
            start = time.perf_counter()
            self.check = Connectivity(self.mgmt_ips, self.username, self.password, self.enable_pw)
            while True:
                self.finished_devices = []
                successful_devices = self.check.successful_devices
                try:
                    if sw_vl_inventory_option:
                        print('Checking Switch VLAN Inventory on devices...')
                        MultiThread(sw_vl_inventory, successful_devices).mt()
                    else:
                        print('Checking VLAN Inventory on devices...')
                        MultiThread(vlan_inventory, successful_devices).mt()
                    if len(self.finished_devices) == len(successful_devices):
                        if sw_vl_inventory_option:
                            output_switches(switch_vlan_inventory)
                        else:
                            output_vlans(vlan_master['vlan_db'])
                        break
                    else:
                        # For debugging
                        bug_devices = []
                        for s_device in successful_devices:
                            if all(s_device['ip'] != f_device for f_device in self.finished_devices):
                                bug_devices.append(s_device)
                        print('Ran into socket bug. Trying again...')
                except ValueError:
                    print('Did not recieve ICMP Echo reply from any device.')
                    break
            failed_devices = self.check.failed_devices
            if len(failed_devices) != 0:
                print('See failed_devices.csv for more information on failed devices')
                output_failed_to_file(failed_devices)
            end = time.perf_counter()
            if sw_vl_inventory_option:
                print(f'Switch VLAN Inventory ran in {int(round(end - start, 0))} seconds.')
                print('See sw_vlans.csv for Switch VLAN Inventory')
            else:
                print(f'VLAN Inventory ran in {int(round(end - start, 0))} seconds.')
                print('See vlans.csv for VLAN Inventory')
            input('Press Enter to close.')


if __name__ == '__main__':
    VlanInventory()
