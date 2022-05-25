from dataclasses import dataclass
from ipaddress import IPv4Address
import json
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from requests import request
import paramiko

import connect


@dataclass
class CreateMachine:
    name: str
    ram_mb: int
    cpu_cores: int
    storage_gb: int
    network_port_group: str
    esxi_node: str
    comment: str


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
            MachineDetail(
                id=vm.get('id'))
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


@app.post("/v1/machine")
def api_create_vm(request: Request):
    req_data = request.get_data()
    req_txt = req_data.decode('utf-8')
    # Get Request body
    payload = json.loads(req_txt)
    # print(payload)
    vm_spec = {
        "name": payload.get('name'),
        "ram": payload.get('ram'),
        "cpu": payload.get('cpu'),
        "storage": payload.get('storage'),
        "network": payload.get('network'),
        "esxi_node": payload.get('esxi_node'),
        "comment": payload.get('comment'),
        "tags": payload.get('tags'),
        "author": "Anonymous"
    }
    result = connect.api_create_vm(vm_spec)
    if result.get('error') is None:
        # correct
        return result
    else:
        # incorrect
        return result


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
