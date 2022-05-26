import pathlib
from dataclasses import asdict, dataclass
from ipaddress import IPv4Address

import paramiko

import connecter
import load_config


@dataclass
class MachineSpecCrawled:
    """ Detail info for existing virtual machines """
    id: int
    name: str
    datastore: str
    datastore_path: pathlib.Path
    guest_os: str
    vm_version: str
    comment: str
    power: connecter.PowerStatus
    ipaddress: IPv4Address
    esxi_node_name: str
    esxi_node_addr: str


def main():
    """ Init ssh connecter """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    """ Load Config """
    machines_info = []
    nodes_conf = load_config.get_esxi_nodes()
    for esxi_nodename, config in nodes_conf.items():
        # try:
        # VMにSSH接続
        cl = client.connect(
            hostname=config.addr,
            username=config.username,
            key_filename=config.identity_file_path
        )
        # except paramiko.ssh_exception.SSHException as e:
        #     print(e)

        # VM一覧を結合
        vm_list: dict[int, connecter.MachineDetail] = connecter.get_vms_list(
            _client=cl)
        vm_power: dict[int, connecter.PowerStatus] = connecter.get_vms_power(
            _client=cl)
        vm_ip: dict[int, IPv4Address] = connecter.get_vms_ip(_client=cl)

        for vmid, machine_detail in vm_list.items():
            power = vm_power.get(vmid, connecter.PowerStatus.UNKNOWN)
            ipaddr = vm_ip.get(vmid, "")
            vm_info = asdict(machine_detail) | {
                "power": power,
                "ipaddr": ipaddr,
                "esxi_node_name": esxi_nodename,
                "esxi_node_addr": config.addr,
            }
            spec = MachineSpecCrawled(**vm_info)
            machines_info.append(spec)


if __name__ == "__main__":
    main()
