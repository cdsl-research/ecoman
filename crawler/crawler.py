import pathlib
from dataclasses import asdict, dataclass
from ipaddress import IPv4Address
from typing import List
import os

import paramiko
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, OperationFailure

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
    ip_address: IPv4Address
    esxi_node_name: str
    esxi_node_address: str


def crawl() -> List[MachineSpecCrawled]:
    """ Init ssh connecter """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()

    """ Load Config """
    machines_info: List[MachineSpecCrawled] = []
    nodes_conf = load_config.get_esxi_nodes()
    for esxi_nodename, config in nodes_conf.items():
        # try:
        # VMにSSH接続
        client.connect(
            config.addr,
            username=config.username,
            key_filename=config.identity_file_path,
            timeout=5.0
        )
        # except paramiko.ssh_exception.SSHException as e:
        #     print(e)

        # VM一覧を結合
        vm_list: dict[int, connecter.MachineDetail] = connecter.get_vms_list(
            _client=client)
        vm_power: dict[int, connecter.PowerStatus] = connecter.get_vms_power(
            _client=client)
        vm_ip: dict[int, IPv4Address] = connecter.get_vms_ip(_client=client)

        for vmid, machine_detail in vm_list.items():
            power = vm_power.get(vmid, connecter.PowerStatus.UNKNOWN)
            ipaddr = vm_ip.get(vmid, "")
            vm_info = asdict(machine_detail) | {
                "power": power,
                "ip_address": ipaddr,
                "esxi_node_name": esxi_nodename,
                "esxi_node_address": config.addr,
            }
            spec = MachineSpecCrawled(**vm_info)
            machines_info.append(spec)
        
    # print(machines_info)
    return machines_info


def register(machines_info: List[MachineSpecCrawled]):
    MONGO_USERNAME = os.getenv("MONGO_USERNAME", "root")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "example")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "machines")
    MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
    # MONGO_CONNECTION_STRING = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}"
    MONGO_CONNECTION_STRING = f"mongodb://{MONGO_HOST}/"

    client = MongoClient(MONGO_CONNECTION_STRING)
    client.admin.command('ping')
    db = client[MONGO_DBNAME]
    # collection = db["machines"]
    from mongo_ipv4_codec import codec_options
    collection = db.get_collection("machines", codec_options=codec_options)

    filter_ = {}
    records = [asdict(msc) for msc in machines_info]
    bulk_replaces = [
        UpdateOne({
            'id': rec['id'], 
            'esxi_node_name': rec['esxi_node_name']
        }, {
            '$set': rec
        }, upsert=True) for rec in records
    ]
    # print(records)
    collection.bulk_write(bulk_replaces)



def main():
    c = crawl()
    register(machines_info=c)


if __name__ == "__main__":
    main()
