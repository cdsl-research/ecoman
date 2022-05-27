from http.client import REQUEST_URI_TOO_LONG
import os
import pathlib
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from ipaddress import IPv4Address
from typing import Dict, List, Any

import paramiko
from pymongo import MongoClient, UpdateOne

import vim_cmd_parser  # noqa

dir_this_file = os.path.dirname(__file__)
parent_dir = os.path.join(dir_this_file, '..')
sys.path.append(parent_dir)

from library import load_config, mongo_ipv4_codec  # noqa


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


@dataclass
class MachineSpec:
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


def get_vm_detail(_client: paramiko.SSHClient, vmid: int) -> dict[str, Any]:
    """ 個別VMの詳細を取得 """

    vm_detail: dict[str, Any] = {}
    _, stdout, _ = _client.exec_command(f'vim-cmd vmsvc/get.summary {vmid}')
    result = vim_cmd_parser.parser(stdout.read().decode().split('\n'))

    runtime = result["vim.vm.Summary"]["runtime"]
    vm_detail["connection_state"] = runtime["connectionState"]
    vm_detail["boot_time"] = runtime["bootTime"]
    vm_detail["max_cpu_usage"] = runtime["maxCpuUsage"]
    vm_detail["max_memory_usage"] = runtime["maxMemoryUsage"]

    guest = result["vim.vm.Summary"]["guest"]
    vm_detail["tools_status"] = guest["toolsStatus"]
    vm_detail["hostname"] = guest["hostName"]
    vm_detail["ip_address"] = guest["ipAddress"]

    config = result["vim.vm.Summary"]["config"]
    vm_detail["name"] = config["name"]
    vm_detail["memory_size_mb"] = config["memorySizeMB"]
    vm_detail["num_cpu"] = config["numCpu"]
    vm_detail["num_ethernet_cards"] = config["numEthernetCards"]
    vm_detail["num_virtual_disks"] = config["numVirtualDisks"]
    vm_detail["guest_fullname"] = config["guestFullName"]

    storage = result["vim.vm.Summary"]["storage"]
    vm_detail["commited"] = storage["committed"]

    quick_stats = result["vim.vm.Summary"]["quickStats"]
    vm_detail["overall_cpu_usage"] = quick_stats["overallCpuUsage"]
    vm_detail["guest_memory_usage"] = quick_stats["guestMemoryUsage"]
    vm_detail["guest_heartbeat_status"] = quick_stats["guestHeartbeatStatus"]
    vm_detail["granted_memory"] = quick_stats["grantedMemory"]
    vm_detail["uptime_seconds"] = quick_stats["uptimeSeconds"]

    vm_detail["overall_status"] = result["vim.vm.Summary"]["overallStatus"]

    return vm_detail


def get_vms_list(_client: paramiko.SSHClient) -> Dict[int, MachineSpec]:
    """ VMのリストを取得 """

    print("Start get_vms_list")
    # VM情報一覧の2行目～を取得(ラベルを除外)
    _, stdout, stderr = _client.exec_command('vim-cmd vmsvc/getallvms')
    print("stderr:", stderr.read())

    vm_info: Dict[int, MachineSpec] = {}
    for line in stdout.readlines():
        # 数字から始まる行
        if re.match(r'^\d+', line):
            try:
                dat = line.strip('\n').split()
                vmid = int(dat[0])
                vm_info[vmid] = MachineSpec(
                    id=vmid,
                    name=dat[1],
                    datastore=dat[2],
                    datastore_path=dat[3],
                    guest_os=dat[4],
                    vm_version=dat[5],
                    comment=' '.join(dat[6:])
                )

                """ VMの詳細をクロール """
                result = get_vm_detail(_client=_client, vmid=vmid)

                # import json
                # print(json.dumps(result, indent=4))

            except Exception as e:
                print("Fail to create MachineSpec: dat=", dat)
                print("Exception: ", e)
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
    print("stderr:", stderr.read())

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
    print("stderr:", stderr.read())

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
        print("+++ Connect to", esxi_nodename, "+++")
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
        vm_list: dict[int, MachineSpec] = get_vms_list(
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
            try:
                spec = MachineSpecCrawled(**vm_info)
                machines_info.append(spec)
            except Exception as e:
                print("Fail to parse as MachineSpecCrawled:", vm_info)
                continue

    # print(machines_info)
    return machines_info


def register(machines_info: List[MachineSpecCrawled]):
    MONGO_USERNAME = os.getenv("MONGO_USERNAME", "")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "ecoman")
    MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
    if MONGO_USERNAME == "":
        credential = ""
    else:
        credential = MONGO_USERNAME + ":"
        if MONGO_PASSWORD:
            credential += MONGO_PASSWORD
        credential += "@"
    MONGO_CONNECTION_STRING = f"mongodb://{credential}{MONGO_HOST}/"

    client = MongoClient(MONGO_CONNECTION_STRING)
    client.admin.command('ping')
    db = client[MONGO_DBNAME]
    collection = db.get_collection(
        "machines", codec_options=mongo_ipv4_codec.codec_options)

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
