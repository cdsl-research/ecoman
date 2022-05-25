import json
import pathlib
from dataclasses import dataclass, asdict
from ipaddress import IPv4Address
from typing import Literal

import paramiko
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests import request

import connect
import load_config
import model


@dataclass
class MachineDetail:
    id: int
    name: str
    esxi_node: str
    power: Literal["on", "off", "suspend", "unknown"]
    ipaddr: IPv4Address


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def page_top(request: Request):
    machines_info = []
    for esxi_nodename, config in load_config.get_esxi_nodes().items():
        try:
            # VMにSSH接続
            connect.client.connect(
                hostname=config.addr,
                username=config.username,
                password=config.password
            )
        except paramiko.ssh_exception.SSHException as e:
            print(e)

        # VM一覧を結合
        vm_list = connect.get_vms_list()
        vm_power = connect.get_vms_power()
        vm_ip = connect.get_vms_ip()

        for vmid, machine_detail in vm_list.items():
            power = vm_power.get(vmid, "unknown")
            ipaddr = vm_ip.get(vmid, "")
            vm_info = asdict(machine_detail) | {
                "power": power,
                "ipaddr": ipaddr,
                "esxi_node_name": esxi_nodename,
                "esxi_node_addr": config.addr,
            }
            machines_info.append(vm_info)

    return templates.TemplateResponse("top.html", {
        "title": "TOP",
        "machines": machines_info,
        "request": request
    })


@app.get("/create", response_class=HTMLResponse)
def page_create_vm(request: Request):
    return templates.TemplateResponse("create.html", {
        "title": "CREATE VM",
        "request": request
    })


@app.get("/machine/{esxi_nodename}/{machine_id}", response_class=HTMLResponse)
def page_read_vm_detail(esxi_nodename: str, machine_id: int):
    return templates.TemplateResponse("detail.html", {
        "title": f"DETAIL: {esxi_nodename} {machine_id}",
        "uniq_id": machine_id,
        "detail": connect.app_detail(f"{esxi_nodename}|{machine_id}"),
        "request": request
    })


@app.get("/v1/machine")
def api_read_vm():
    pass


@dataclass
class CreateMachineRequest:
    """ Request schema for creating a virtual machine """
    name: str
    ram_mb: int
    cpu_cores: int
    storage_gb: int
    network_port_group: str
    esxi_nodename: str
    comment: str
    author: str


@app.post("/v1/machine")
def api_create_vm(machine_req_req: CreateMachineRequest):
    # encode recieved request
    machine_req_req_enc = jsonable_encoder(machine_req_req)
    # validate and convert datamodel
    machine_req: model.CreateMachineSpec = validate_machine_req(
        machine_req=machine_req_req_enc)

    # Create Virtual Machine
    result: model.CreateMchineResult = connect.create_vm(
        machine_req=machine_req)
    if result.status == model.ProcessResult.NG:  # failed
        print("Fail to create VM:", result.message)
    return result


def validate_machine_req(machine_req: CreateMachineRequest) -> model.CreateMachineSpec:
    """ 仮想マシンの仕様を検証 """

    # NAME
    if machine_req.name:
        name: str = machine_req.name.lower()
    else:
        import random
        suffix = str(random.randint(0, 999)).zfill(3)
        name = f"machine-{suffix}"

    # RAM
    if 512 <= machine_req.ram_mb <= 8192:
        ram_mb: int = machine_req.ram_mb
    else:
        ram_mb = 512

    # CPU
    if 1 <= machine_req.cpu_cores:
        cpu_cores: int = machine_req.cpu_cores
    else:
        machine_req.cpu_cores = 1

    # Storage
    if 30 <= machine_req.storage_gb <= 100:
        storage_gb: int = machine_req.storage_gb
    else:
        storage_gb = 30

    # Network
    if machine_req.network_port_group:
        network_port_group: str = machine_req.network_port_group
    else:
        network_port_group = "VM Network"

    # ESXi Node
    conf = load_config.get_esxi_nodes()
    esxi_nodenames = tuple(conf.keys())  # get ESXi Node List
    if machine_req.esxi_nodename in esxi_nodenames:
        esxi_nodename: str = machine_req.esxi_nodename
    else:
        esxi_nodename: str = random.choice(esxi_nodenames)

    # Datastore Path, Installer ISO Path
    esxi_node_config: load_config.HostsConfig = conf[machine_req.esxi_nodename]
    datastore_path: pathlib.Path = esxi_node_config.datastore_path
    installer_iso_path = esxi_node_config.installer_iso_path

    # Comment, Author
    comment = ", ".join(f"Author: '{machine_req.author}'",
                        f"Comment: '{machine_req.comment}'")

    return model.CreateMachineSpec(
        name=name,
        ram_mb=ram_mb,
        cpu_cores=cpu_cores,
        storage_gb=storage_gb,
        network_port_group=network_port_group,
        esxi_nodename=esxi_nodename,
        datastore_path=datastore_path,
        installer_iso_path=installer_iso_path,
        comment=comment
    )


@app.get("/v1/machine/{esxi_nodename}/{machine_id}")
def api_read_vm(esxi_nodename: str, machine_id: int):
    return connect.get_vm_detail(esxi_nodename, machine_id)


@app.put("/v1/machine/{esxi_nodename}/{machine_id}/power")
def api_update_vm_power(esxi_nodename: str, machine_id: int, request: Request):
    # Parse Request
    req_data = request.get_data()
    req_txt = req_data.decode('utf-8')
    payload = json.loads(req_txt)
    # Get Request status
    power_state = payload.get('state')
    # Change status
    result: str = connect.set_vm_power(
        esxi_nodename=esxi_nodename,
        vmid=machine_id,
        power_state=power_state
    )
    return {"status": "ok", "detail": result}
