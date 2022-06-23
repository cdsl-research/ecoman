import os
import pathlib
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List

import load_config
import paramiko
import vim_cmd_parser
from pymongo import MongoClient, UpdateOne


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


@dataclass
class MachineDetail:
    power: PowerStatus  # "poweredOn"
    boot_time: datetime  # "2022-04-19T11:27:12Z"
    tools_status: str  # "toolsOk"
    hostname: str  # "koyama-main"
    ip_address: str  # "192.168.100.236"
    name: str  # "koyama-main"
    memory_size_mb: int  # 4096
    num_cpu: int  # 2
    num_ethernet_cards: int  # 1
    num_virtual_disks: int  # 1
    guest_fullname: str  # "Ubuntu Linux (64-bit)"
    storage_commited: int  # 10684206203
    overall_cpu_usage: int  # 170
    guest_memory_usage: int  # 491
    uptime_seconds: int  # 3290727
    overall_status: str  # "green"


@dataclass
class MachineDetailWithOptions(MachineDetail):
    id: int
    datastore: str
    datastore_path: pathlib.Path
    comment: str


@dataclass
class MachineDetailForStore(MachineDetailWithOptions):
    esxi_node_name: str
    esxi_node_address: str
    updated_at: datetime


def get_vm_detail(_client: paramiko.SSHClient, vmid: int) -> MachineDetail:
    """個別VMの詳細を取得"""

    _, stdout, _ = _client.exec_command(f"vim-cmd vmsvc/get.summary {vmid}")
    result = vim_cmd_parser.parser(stdout.read().decode().split("\n"))
    runtime = result["vim.vm.Summary"]["runtime"]
    guest = result["vim.vm.Summary"]["guest"]
    config = result["vim.vm.Summary"]["config"]
    storage = result["vim.vm.Summary"]["storage"]
    quick_stats = result["vim.vm.Summary"]["quickStats"]

    if runtime["powerState"] == "poweredOn":
        power_status = PowerStatus.ON
    elif runtime["powerState"] == "poweredOff":
        power_status = PowerStatus.OFF
    elif runtime["powerState"] == "suspended":
        power_status = PowerStatus.SUSPEND
    else:
        power_status = PowerStatus.UNKNOWN

    if guest["ipAddress"] is None:
        ipaddress_ = ""
    else:
        ipaddress_ = guest["ipAddress"]

    vm_detail = MachineDetail(
        power=power_status,
        boot_time=runtime["bootTime"],
        tools_status=guest["toolsStatus"],
        hostname=guest["hostName"],
        ip_address=ipaddress_,
        name=config["name"],
        memory_size_mb=config["memorySizeMB"],
        num_cpu=config["numCpu"],
        num_ethernet_cards=config["numEthernetCards"],
        num_virtual_disks=config["numVirtualDisks"],
        guest_fullname=config["guestFullName"],
        storage_commited=storage["committed"],
        overall_cpu_usage=quick_stats["overallCpuUsage"],
        guest_memory_usage=quick_stats["guestMemoryUsage"],
        uptime_seconds=quick_stats.get("uptimeSeconds", 0),
        overall_status=result["vim.vm.Summary"]["overallStatus"],
    )
    return vm_detail


def get_vms_list(
        _client: paramiko.SSHClient) -> Dict[int, MachineDetailWithOptions]:
    """VMのリストを取得"""

    print("Start get_vms_list")
    # VM情報一覧の2行目～を取得(ラベルを除外)
    _, stdout, stderr = _client.exec_command("vim-cmd vmsvc/getallvms")
    print("stderr:", stderr.read())

    vm_info: Dict[int, MachineDetailWithOptions] = {}
    for line in stdout.readlines():
        # 数字から始まる行
        if re.match(r"^\d+", line):
            try:
                """VMの詳細をクロール"""
                dat = line.strip("\n").split()
                vmid = int(dat[0])
                result: MachineDetail = get_vm_detail(
                    _client=_client, vmid=vmid)
                vm_info[vmid] = MachineDetailWithOptions(
                    **asdict(result),
                    id=vmid,
                    datastore=dat[2],
                    datastore_path=dat[3],
                    comment=" ".join(dat[6:]),
                )

                # import json
                # print(json.dumps(result, indent=4))

            except Exception as e:
                print("Fail to create MachineDetailSpec: dat=", dat)
                print("Exception: ", e)
                continue

        # Vmidから始まる行
        elif line.startswith("Vmid"):
            continue

    return vm_info


def crawl() -> List[MachineDetailForStore]:
    print("Start crawling")

    """ Init ssh connecter """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    """ Load Config """
    machines_info: List[MachineDetailForStore] = []
    nodes_conf = load_config.get_esxi_nodes()
    for esxi_nodename, config in nodes_conf.items():
        print("+++ Connect to", esxi_nodename, "+++")
        try:
            client.connect(
                config.addr,
                username=config.username,
                key_filename=config.identity_file_path,
                timeout=5.0,
            )
        except Exception as e:
            print(e)
            continue

        # VM一覧を結合
        vm_list: dict[int, MachineDetailWithOptions] = get_vms_list(
            _client=client)

        for _, machine_detail in vm_list.items():
            try:
                vm_info = MachineDetailForStore(
                    **asdict(machine_detail),
                    esxi_node_name=esxi_nodename,
                    esxi_node_address=config.addr,
                    updated_at=datetime.now(),
                )
                machines_info.append(vm_info)
            except Exception as e:
                print("Fail to parse as MachineDetailForStore:", e)
                continue

        client.close()

    # print(machines_info)
    return machines_info


def register(machines_info: List[MachineDetailForStore]):
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
    client.admin.command("ping")
    db = client[MONGO_DBNAME]
    collection = db.get_collection("machines")

    bulk_replaces = [
        UpdateOne(
            {"id": rec.id, "esxi_node_name": rec.esxi_node_name},
            {"$set": asdict(rec)},
            upsert=True,
        )
        for rec in machines_info
    ]
    # print(records)
    collection.bulk_write(bulk_replaces)


def main():
    print("Starting crawler loop")
    crawl_interval = int(os.getenv("CRAWLER_INTERVAL", "60"))
    print("Crawl interval =", crawl_interval, "[sec]")

    while True:
        start_at = time.time()
        c = crawl()
        register(machines_info=c)
        consumed = time.time() - start_at
        if crawl_interval - consumed < 0:
            consumed += crawl_interval
        print("waiting for next crawl:", consumed, "[sec]")
        time.sleep(crawl_interval - consumed)


if __name__ == "__main__":
    main()
