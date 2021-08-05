import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from icmplib import ping
from netmiko import ConnectHandler, ssh_exception, SSHDetect

from address_validator import ipv4

# Checks for TextFSM templates within single file bundle if code is frozen
if getattr(sys, 'frozen', False):
    os.environ['NET_TEXTFSM'] = sys._MEIPASS
else:
    os.environ['NET_TEXTFSM'] = './templates'


class MgmtIPAddresses:
    """Input .txt file location containing list of management IP addresses"""
    def __init__(self, mgmt_file_location):
        self.mgmt_file_location = mgmt_file_location
        self.mgmt_ips = []
        """Formatted set of validated IP addresses"""
        self.invalid_line_nums = []
        """Set of invalid line numbers corresponding to line number of management file input"""
        self.invalid_ip_addresses = []
        """Set of invalid IP addresses"""
        self.validate = True
        """Bool of management IP address file input validation"""
        with open(self.mgmt_file_location) as file:
            for idx, address in enumerate(file):
                ip_address = str(address).strip('\n')
                if ipv4(ip_address) is False:
                    self.invalid_line_nums.append(str(idx + 1))
                    self.invalid_ip_addresses.append(str(address))
                    self.validate = False
                    """Bool of management IP address file input validation"""
                else:
                    self.mgmt_ips.append(ip_address)


def reachability(ip_address, count=4):
    """Returns bool if host is reachable with default count of 4 pings"""
    return ping(ip_address, privileged=False, count=count).is_alive


class Connection:
    """SSH or TELNET Connection Initiator"""
    def __init__(self, ip_address, username, password, devicetype='autodetect', enable=False, enable_pw=''):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = ''
        self.devicetype = devicetype
        self.con_type = None
        self.exception = 'None'
        self.authentication = False
        self.authorization = False
        self.connectivity = False
        self.session = None
        self.enable = enable
        self.enable_pw = enable_pw
        self.device = {
            'device_type': self.devicetype,
            'ip': ip_address,
            'username': username,
            'password': password,
            'fast_cli': False
        }
        if self.enable:
            self.device['secret'] = self.enable_pw

    def check(self):
        """Base connectivity check method of device returning updated self attributes:\n
        devicetype\n
        hostname\n
        con_type\n
        exception\n
        authentication\n
        authorization\n
        connectivity"""

        def device_check(device):
            while True:
                if self.enable:
                    with ConnectHandler(**device) as session:
                        session.enable()
                        if not session.send_command('show run', delay_factor=4).__contains__('Invalid input detected'):
                            self.authorization = True
                    break
                else:
                    with ConnectHandler(**device) as session:
                        showver = session.send_command('show version', delay_factor=4, use_textfsm=True)
                        if not showver.__contains__('Failed'):
                            self.hostname = showver[0]['hostname']
                            if session.send_command('show run', delay_factor=4).__contains__('Invalid input detected'):
                                self.enable = True
                                self.device['secret'] = self.enable_pw
                            else:
                                self.authorization = True
                                break
                        else:
                            break

        if reachability(self.ip_address):
            try:
                try:
                    autodetect = SSHDetect(**self.device).autodetect()
                    self.device['device_type'] = autodetect
                    self.devicetype = autodetect
                    device_check(self.device)
                except ValueError:
                    try:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        device_check(self.device)
                    except ValueError:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        device_check(self.device)
                self.authentication = True
                self.connectivity = True
                self.con_type = 'SSH'
            except (ConnectionRefusedError, ValueError, ssh_exception.NetmikoAuthenticationException,
                    ssh_exception.NetmikoTimeoutException):
                try:
                    try:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        device_check(self.device)
                        self.authentication = True
                        self.connectivity = True
                        self.con_type = 'TELNET'
                    except ssh_exception.NetmikoAuthenticationException:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        device_check(self.device)
                        self.authentication = True
                        self.connectivity = True
                        self.con_type = 'TELNET'
                except ssh_exception.NetmikoAuthenticationException:
                    self.connectivity = True
                    self.exception = 'NetmikoAuthenticationException'
                except ssh_exception.NetmikoTimeoutException:
                    self.exception = 'NetmikoTimeoutException'
                except ConnectionRefusedError:
                    self.exception = 'ConnectionRefusedError'
                except ValueError:
                    self.exception = 'ValueError'
                except TimeoutError:
                    self.exception = 'TimeoutError'
            except OSError:
                self.exception = 'OSError'
        else:
            self.exception = 'NoPingEcho'
        return self

    def connection(self):
        """Base connection method\n
        Should only use self attributes:\n
        session\n
        exception"""
        if reachability(self.ip_address):
            try:
                self.session = ConnectHandler(**self.device)
                if self.enable:
                    self.session.enable()
            except ConnectionRefusedError:
                self.exception = 'ConnectionRefusedError'
            except ssh_exception.NetmikoAuthenticationException:
                self.exception = 'NetmikoAuthenticationException'
            except ssh_exception.NetmikoTimeoutException:
                self.exception = 'NetmikoTimeoutException'
            except ValueError:
                self.exception = 'ValueError'
            except TimeoutError:
                self.exception = 'TimeoutError'
            except OSError:
                self.exception = 'OSError'
        else:
            self.exception = 'NoPingEcho'
        return self


class MultiThread:
    """Multithread Initiator"""
    def __init__(self, function=None, iterable=None, successful_devices=None, failed_devices=None, threads=50):
        self.successful_devices = successful_devices
        self.failed_devices = failed_devices
        self.iterable = iterable
        self.threads = threads
        self.function = function
        self.iter_len = len(iterable)

    def mt(self):
        """Executes multithreading on provided function and iterable"""
        if self.iter_len < 50:
            self.threads = self.iter_len
        executor = ThreadPoolExecutor(self.threads)
        futures = [executor.submit(self.function, val) for val in self.iterable]
        wait(futures, timeout=None)
        return self

    def bug(self):
        """Returns bool if Windows PyInstaller bug is present with provided lists for successful and failed devices"""
        successful = len(self.successful_devices)
        failed = len(self.failed_devices)
        if (successful + failed) == self.iter_len:
            return False
        else:
            return True


class Connectivity:
    """Checks connectivity of list of IP addresses asyncronously and checks for windows frozen code socket bug\n
    Returns self attributes:\n
    successful_devices = [{\n
    'ip'\n
    'hostname'\n
    'con_type'\n
    'device_type'\n
    'enable'}]\n
    failed_devices = [{\n
    'ip'\n
    'exception'\n
    'connectivitiy'\n
    'authentication'\n
    'authorization'\n}]"""
    def __init__(self, mgmt_ip_list, username, password, enable_pw=''):
        def check(ip):
            conn = Connection(ip, username, password, enable_pw=enable_pw).check()
            # print(ip)
            if conn.authorization:
                self.successful_devices.append(
                    {
                        'ip': ip,
                        'hostname': conn.hostname,
                        'con_type': conn.con_type,
                        'device_type': conn.devicetype,
                        'enable': conn.enable
                    }
                )
            else:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'exception': conn.exception,
                        'connectivity': conn.connectivity,
                        'authentication': conn.authentication,
                        'authorization': conn.authorization
                    }
                )

        while True:
            self.successful_devices = []
            self.failed_devices = []
            d = MultiThread(check, mgmt_ip_list).mt()
            bug = MultiThread(
                iterable=d.iterable,
                successful_devices=self.successful_devices,
                failed_devices=self.failed_devices
            ).bug()
            if bug:
                time.sleep(7)
            else:
                break
