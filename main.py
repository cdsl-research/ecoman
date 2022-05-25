from dataclasses import dataclass
from ipaddress import IPv4Address
import json
import pathlib
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from requests import request
import paramiko

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
    return templates.TemplateResponse("top.html", {
        "title": "TOP",
        "machines": connect.app_top(),
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
    vm_formated_info = []
    for hostname, param in connect.get_esxi_nodes().items():
        try:
            # VMにSSH接続
            connect.client.connect(
                hostname=param.get('addr'),
                username=param.get('username'),
                password=param.get('password')
            )
        except paramiko.ssh_exception.SSHException as e:
            print(e)

        # VM一覧を結合
        vm_list = connect.get_vms_list()
        vm_power = connect.get_vms_power()
        vm_ip = connect.get_vms_ip()
        for vm in vm_list:
            vm['uniq_id'] = hostname + '|' + vm.get('id')
            vm['esxi_host'] = hostname
            vm['esxi_addr'] = param.get('addr')
            try:
                vm['power'] = vm_power[vm['id']]
            except KeyError:
                vm['power'] = 'error'
            try:
                vm['ipaddr'] = vm_ip[vm['id']]
            except KeyError:
                vm['ipaddr'] = 'unknown'
        vm_formated_info.extend(vm_list)

    return vm_formated_info


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
def api_create_vm(machine_spec_req: model.CreateMachineRequest):
    # encode recieved request
    machine_spec_req_enc = jsonable_encoder(machine_spec_req)
    # validate and convert datamodel
    machine_spec: model.CreateMachineSpec = validate_machine_spec(
        machine_req=machine_spec_req_enc)

    # Create Virtual Machine
    result: model.CreateMchineResult = connect.create_vm(
        machine_spec=machine_spec)
    if result.status == model.ProcessResult.NG:  # failed
        print("Fail to create VM:", result.message)
    return result


def validate_machine_spec(machine_req: model.CreateMachineRequest) -> model.CreateMachineSpec:
    """ 仮想マシンの仕様を検証 """

    # NAME
    if machine_spec.name:
        name: str = machine_spec.name.lower()
    else:
        import random
        suffix = str(random.randint(0, 999)).zfill(3)
        name = f"machine-{suffix}"

    # RAM
    if 512 <= machine_spec.ram_mb <= 8192:
        ram_mb: int = machine_spec.ram_mb
    else:
        ram_mb = 512

    # CPU
    if 1 <= machine_spec.cpu_cores:
        cpu_cores: int = machine_spec.cpu_cores
    else:
        machine_spec.cpu_cores = 1

    # Storage
    if 30 <= machine_spec.storage_gb <= 100:
        storage_gb: int = machine_spec.storage_gb
    else:
        storage_gb = 30

    # Network
    if machine_spec.network_port_group:
        network_port_group: str = machine_spec.network_port_group
    else:
        network_port_group = "VM Network"

    # ESXi Node
    conf = load_config.get_esxi_nodes()
    esxi_nodenames = tuple(conf.keys())  # get ESXi Node List
    if machine_spec.esxi_nodename in esxi_nodenames:
        esxi_nodename: str = machine_spec.esxi_nodename
    else:
        esxi_nodename: str = random.choice(esxi_nodenames)

    # Datastore Path, Installer ISO Path
    esxi_node_config: load_config.HostsConfig = conf[machine_spec.esxi_nodename]
    datastore_path: pathlib.Path = esxi_node_config.datastore_path
    installer_iso_path = esxi_node_config.installer_iso_path

    # Comment, Author
    comment = ", ".join(f"Author: '{machine_spec.author}'",
                        f"Comment: '{machine_spec.comment}'")

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
