import os
import sys

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from requests import request

dir_this_file = os.path.dirname(__file__)
parent_dir = os.path.join(dir_this_file, '..')
sys.path.append(parent_dir)

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


@app.get("/", response_class=HTMLResponse)
def page_top(request: Request):
    collection = db.get_collection("machines")
    response = list(collection.find({}, {'_id': 0}))
    result = sorted(response, key=lambda x: (x['esxi_node_name'], x['id']))
    return templates.TemplateResponse("top.html", {
        "title": "Top",
        "machines": result,
        "request": request
    })


@app.get("/create", response_class=HTMLResponse)
def page_create_vm(request: Request):
    return templates.TemplateResponse("create.html", {
        "title": "Create VM",
        "request": request
    })


@app.get("/machine/{esxi_node_name}/{machine_id}", response_class=HTMLResponse)
def page_read_vm_detail(esxi_node_name: str, machine_id: int):
    collection = db.get_collection(
        "machines", codec_options=mongo_ipv4_codec.codec_options)
    filter_ = {
        "esxi_node_name": esxi_node_name,
        "id": machine_id
    }
    entry = collection.find_one(filter_, {'_id': 0})
    print(entry)

    return templates.TemplateResponse("detail.html", {
        "title": f"Detail: {esxi_node_name} {machine_id}",
        "request": request
    })


# @dataclass
# class CreateMachineRequest:
#     """ Request schema for creating a virtual machine """
#     name: str
#     ram_mb: int
#     cpu_cores: int
#     storage_gb: int
#     network_port_group: str
#     esxi_nodename: str
#     comment: str
#     author: str


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
