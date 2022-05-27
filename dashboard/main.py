import json
import pathlib
from dataclasses import dataclass, asdict
from ipaddress import IPv4Address
from typing import Literal
import os
from datetime import datetime

import paramiko
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests import request
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, OperationFailure

from mongo_ipv4_codec import codec_options




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


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


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


@app.get("/", response_class=HTMLResponse)
def page_top(request: Request):
    collection = db.get_collection("machines", codec_options=codec_options)
    response = list(collection.find({}, {'_id': 0}))
    result = sorted(response, key=lambda x: (x['esxi_node_name'], x['id']))
    return templates.TemplateResponse("top.html", {
        "title": "TOP",
        "machines": result,
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
        "detail": connecter.app_detail(f"{esxi_nodename}|{machine_id}"),
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


# @app.post("/v1/machine")
# def api_create_vm(machine_req_req: CreateMachineRequest):
#     # encode recieved request
#     machine_req_req_enc = jsonable_encoder(machine_req_req)
#     # validate and convert datamodel
#     machine_req: model.CreateMachineSpec = validate_machine_req(
#         machine_req=machine_req_req_enc)

#     # Create Virtual Machine
#     result: model.CreateMchineResult = connecter.create_vm(
#         machine_req=machine_req)
#     if result.status == model.ProcessResult.NG:  # failed
#         print("Fail to create VM:", result.message)
#     return result


# def validate_machine_req(machine_req: CreateMachineRequest) -> model.CreateMachineSpec:
#     """ 仮想マシンの仕様を検証 """

#     # NAME
#     if machine_req.name:
#         name: str = machine_req.name.lower()
#     else:
#         import random
#         suffix = str(random.randint(0, 999)).zfill(3)
#         name = f"machine-{suffix}"

#     # RAM
#     if 512 <= machine_req.ram_mb <= 8192:
#         ram_mb: int = machine_req.ram_mb
#     else:
#         ram_mb = 512

#     # CPU
#     if 1 <= machine_req.cpu_cores:
#         cpu_cores: int = machine_req.cpu_cores
#     else:
#         machine_req.cpu_cores = 1

#     # Storage
#     if 30 <= machine_req.storage_gb <= 100:
#         storage_gb: int = machine_req.storage_gb
#     else:
#         storage_gb = 30

#     # Network
#     if machine_req.network_port_group:
#         network_port_group: str = machine_req.network_port_group
#     else:
#         network_port_group = "VM Network"

#     # ESXi Node
#     conf = load_config.get_esxi_nodes()
#     esxi_nodenames = tuple(conf.keys())  # get ESXi Node List
#     if machine_req.esxi_nodename in esxi_nodenames:
#         esxi_nodename: str = machine_req.esxi_nodename
#     else:
#         esxi_nodename: str = random.choice(esxi_nodenames)

#     # Datastore Path, Installer ISO Path
#     esxi_node_config: load_config.HostsConfig = conf[machine_req.esxi_nodename]
#     datastore_path: pathlib.Path = esxi_node_config.datastore_path
#     installer_iso_path = esxi_node_config.installer_iso_path

#     # Comment, Author
#     comment = ", ".join(f"Author: '{machine_req.author}'",
#                         f"Comment: '{machine_req.comment}'")

#     return model.CreateMachineSpec(
#         name=name,
#         ram_mb=ram_mb,
#         cpu_cores=cpu_cores,
#         storage_gb=storage_gb,
#         network_port_group=network_port_group,
#         esxi_nodename=esxi_nodename,
#         datastore_path=datastore_path,
#         installer_iso_path=installer_iso_path,
#         comment=comment
#     )


# @app.get("/v1/machine/{esxi_nodename}/{machine_id}")
# def api_read_vm(esxi_nodename: str, machine_id: int):
#     return connecter.get_vm_detail(esxi_nodename, machine_id)


# @app.put("/v1/machine/{esxi_nodename}/{machine_id}/power")
# def api_update_vm_power(esxi_nodename: str, machine_id: int, request: Request):
#     # Parse Request
#     req_data = request.get_data()
#     req_txt = req_data.decode('utf-8')
#     payload = json.loads(req_txt)
#     # Get Request status
#     power_state = payload.get('state')
#     # Change status
#     result: str = connecter.set_vm_power(
#         esxi_nodename=esxi_nodename,
#         vmid=machine_id,
#         power_state=power_state
#     )
#     return {"status": "ok", "detail": result}
