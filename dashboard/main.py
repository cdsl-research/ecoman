import datetime
import os
import xmlrpc.client
from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

import load_config  # noqa


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


class ProcessResult:
    OK: int = "ok"
    NG: int = "ng"


@dataclass
class RequestUpdatePowerStatus:
    status: Literal["on", "off", "suspend", "shutdown", "reset", "reboot"]


EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS", "127.0.0.1")
EXECUTOR_PORT = int(os.getenv("EXECUTOR_PORT", "8600"))
print("EXECUTOR TARGET:", EXECUTOR_ADDRESS, EXECUTOR_PORT)

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


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def page_top(request: Request):
    collection = db.get_collection("machines")
    cur_date = datetime.datetime.now()
    response = list(
        collection.find(
            {"updated_at": {"$gte": cur_date - datetime.timedelta(minutes=10)}},
            {"_id": 0},
        )
    )
    result = sorted(response, key=lambda x: (x["esxi_node_name"], x["id"]))
    return templates.TemplateResponse(
        "top.html",
        {
            "title": "Top",
            "machines": result,
            "threshold": {
                "cpu": int(os.getenv("DASHBOARD_THRESHOLD_CPU", "5")),
                "ram_mb": int(os.getenv("DASHBOARD_THRESHOLD_RAM_MB", "8192")),
                "storage_gb": int(os.getenv("DASHBOARD_THRESHOLD_STORAGE_GB", "50")),
            },
            "request": request,
        },
    )


@app.get("/nodes", response_class=HTMLResponse)
def page_esxi_nodes(request: Request):
    esxi_nodes = load_config.get_esxi_nodes()
    return templates.TemplateResponse(
        "node.html",
        {"title": "ESXi Nodes", "request": request, "esxi_nodes": esxi_nodes},
    )


@app.get("/create", response_class=HTMLResponse)
def page_create_vm(request: Request):
    esxi_nodes = load_config.get_esxi_nodes()
    active_esxi_nodes = set()
    for nodename, detail in esxi_nodes.items():
        if len(detail.datastore_path) > 0:
            active_esxi_nodes.add(nodename)
    return templates.TemplateResponse(
        "create.html",
        {"title": "Create VM", "request": request, "esxi_nodes": active_esxi_nodes},
    )


@app.get("/machine/{esxi_node_name}/{machine_id}", response_class=HTMLResponse)
def page_read_vm_detail(esxi_node_name: str, machine_id: int, request: Request):
    collection = db.get_collection("machines")
    filter_ = {"esxi_node_name": esxi_node_name, "id": machine_id}
    machine = collection.find_one(filter_, {"_id": 0})

    return templates.TemplateResponse(
        "detail.html",
        {
            "title": f"Detail: {esxi_node_name} {machine_id}",
            "machine": machine,
            "request": request,
        },
    )


@app.put("/v1/machine/{esxi_node_name}/{machine_id}/power")
def api_update_vm_power(
    esxi_node_name: str, machine_id: int, power_status: RequestUpdatePowerStatus
):
    power_state = jsonable_encoder(power_status)["status"]
    with xmlrpc.client.ServerProxy(
        f"http://{EXECUTOR_ADDRESS}:{EXECUTOR_PORT}/"
    ) as proxy:
        result = proxy.set_vm_power(esxi_node_name, machine_id, power_state)

    if result.get("result") == ProcessResult.NG:
        raise HTTPException(status_code=503, detail=result.get("message"))
    return result


@dataclass
class CreateMachineRequest:
    """Request schema for creating a virtual machine"""

    name: str
    ram_mb: int
    cpu_cores: int
    storage_gb: int
    esxi_nodename: str
    comment: str


@app.post("/v1/machine")
def api_create_vm(machine_req: CreateMachineRequest):
    with xmlrpc.client.ServerProxy(
        f"http://{EXECUTOR_ADDRESS}:{EXECUTOR_PORT}/"
    ) as proxy:
        result = proxy.create_vm(
            machine_req.name,  # _name 'ecoman-example3'
            machine_req.ram_mb,  # _ram_mb 512
            machine_req.cpu_cores,  # _cpu_cores 1
            machine_req.storage_gb,  # _storage_gb 30
            machine_req.esxi_nodename,  # "jasmine"
            machine_req.comment,
        )

    if result.get("result") == ProcessResult.NG:  # failed
        raise HTTPException(status_code=503, detail=result.get("message"))
    return result
