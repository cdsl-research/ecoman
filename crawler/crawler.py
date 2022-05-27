import pathlib
from dataclasses import asdict, dataclass
from ipaddress import IPv4Address
from typing import List, Dict
import re
import os
from datetime import datetime
import ipaddress


import paramiko
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, OperationFailure

from mongo_ipv4_codec import codec_options
import load_config


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


@dataclass
class MachineDetail:
    id: int
    name: str
    datastore: str
    datastore_path: pathlib.Path
    guest_os: str
    vm_version: str
    comment: str


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
    power: PowerStatus
    ip_address: IPv4Address
    esxi_node_name: str
    esxi_node_address: str
    updated_at: datetime



def get_vms_list(_client: paramiko.SSHClient) -> Dict[int, MachineDetail]:
    """ VMのリストを取得 """

    print("Start get_vms_list")
    # VM情報一覧の2行目～を取得(ラベルを除外)
    _, stdout, stderr = _client.exec_command('vim-cmd vmsvc/getallvms')
    print("stderr:", stderr)

    vm_info: Dict[int, MachineDetail] = {}
    for line in stdout.readlines():
        # 数字から始まる行
        if re.match(r'^\d+', line):
            try:
                dat = line.strip('\n').split()
                vmid = int(dat[0])
                vm_info[vmid] = MachineDetail(
                    id=vmid,
                    name=dat[1],
                    datastore=dat[2],
                    datastore_path=dat[3],
                    guest_os=dat[4],
                    vm_version=dat[5],
                    comment=' '.join(dat[6:])
                )
            except Exception as e:
                print("Fail to create MachineDetail: dat=", dat)
                continue

        # Vmidから始まる行
        elif line.startswith("Vmid"):
            continue

    return vm_info


def get_vms_power(_client: paramiko.SSHClient) -> Dict[int, PowerStatus]:
    """ VMの電源状態のリストを取得 """

    print("Start get_vms_power")
    # VMの電源一覧を取得
    _, stdout, stderr = _client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/power.getstate $id | grep -v Retrieved | sed "s/^/$id|/g" &
    done
    """)
    print("stderr:", stderr)

    # VMの電源一覧を整形
    result: Dict[int, PowerStatus] = {}
    for line in stdout.readlines():
        try:
            _vmid, state = line.split('|')
            vmid = int(_vmid)
        except Exception as e:
            print("Exception:", e)
            continue

        if 'Suspended' in state:
            result[vmid] = PowerStatus.SUSPEND
        elif 'Powered on' in state:
            result[vmid] = PowerStatus.ON
        elif 'Powered off' in state:
            result[vmid] = PowerStatus.OFF
        else:
            print("Power unknown: vmid =", vmid)
            result[vmid] = PowerStatus.UNKNOWN

    return result


def get_vms_ip(_client: paramiko.SSHClient) -> Dict[int, IPv4Address]:
    """ VMのIPアドレスのリストを取得 """

    print("Start get_vms_ip")
    _, stdout, stderr = _client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/get.summary $id | grep ipAddress | grep -o \"[0-9a-f:\.]\\+\" | sed "s/\"//g;s/^/$id|/g" &
    done
    """)
    print("stderr:", stderr)

    result: Dict[int, IPv4Address] = {}
    for line in stdout.readlines():
        try:
            vmid, ipaddr = line.split('|')
            result[int(vmid)] = IPv4Address(ipaddr.strip())
        except Exception as e:
            print("Exception", e)
            continue

    return result


def crawl() -> List[MachineSpecCrawled]:
    print("Start crawling")

    """ Init ssh connecter """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    """ Load Config """
    machines_info: List[MachineSpecCrawled] = []
    nodes_conf = load_config.get_esxi_nodes()
    for esxi_nodename, config in nodes_conf.items():
        print("Connect to", esxi_nodename)
        try:
            client.connect(
                config.addr,
                username=config.username,
                key_filename=config.identity_file_path,
                timeout=5.0
            )
        except paramiko.ssh_exception.SSHException as e:
            print(e)
            continue

        # VM一覧を結合
        vm_list: dict[int, MachineDetail] = get_vms_list(
            _client=client)
        vm_power: dict[int, PowerStatus] = get_vms_power(
            _client=client)
        vm_ip: dict[int, IPv4Address] = get_vms_ip(_client=client)

        for vmid, machine_detail in vm_list.items():
            power = vm_power.get(vmid, PowerStatus.UNKNOWN)
            ipaddr = vm_ip.get(vmid, "")
            vm_info = asdict(machine_detail) | {
                "power": power,
                "ip_address": ipaddr,
                "esxi_node_name": esxi_nodename,
                "esxi_node_address": config.addr,
                "updated_at": datetime.now()
            }
            spec = MachineSpecCrawled(**vm_info)
            machines_info.append(spec)
        
    # print(machines_info)
    return machines_info


def register(machines_info: List[MachineSpecCrawled]):
    MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "ecoman")
    MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
    # MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}"
    MONGO_CONNECTION_STRING = f"mongodb://{MONGO_HOST}/"

    client = MongoClient(MONGO_CONNECTION_STRING)
    client.admin.command('ping')
    db = client[MONGO_DBNAME]
    collection = db.get_collection("machines", codec_options=codec_options)

    bulk_replaces = [
        UpdateOne({
            'id': rec.id, 
            'esxi_node_name': rec.esxi_node_name
        }, {
            '$set': asdict(rec)
        }, upsert=True) for rec in machines_info
    ]
    # print(records)
    collection.bulk_write(bulk_replaces)



def main():
    c = crawl()
    register(machines_info=c)


if __name__ == "__main__":
    main()
