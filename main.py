import json

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from requests import request

import connect

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def page_top(request: Request):
    return templates.TemplateResponse("top.html", {
        "title": "TOP",
        "machines": connect.app_top(),
        "request": request
    })


@app.get("/create")
def page_create_vm():
    return templates.TemplateResponse("create.html", {
        "title": "CREATE VM",
        "request": request
    })


@app.get("/machine/{esxi_nodename}/{machine_id}")
def page_read_vm_detail(esxi_nodename:str, machine_id: int):
    return templates.TemplateResponse("detail.html", {
        "title": f"DETAIL: {esxi_nodename} {machine_id}",
        "uniq_id": machine_id,
        "detail": connect.app_detail(f"{esxi_nodename}|{machine_id}"),
        "request": request
    })


@app.get("/v1/machine")
def api_read_vm():
    return connect.app_top()


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
def api_read_vm(esxi_nodename:str, machine_id: int):
    uniq_id = f"{esxi_nodename}|{machine_id}"
    return connect.app_detail(uniq_id)


@app.put("/v1/machine/{esxi_nodename}/{machine_id}/power")
def api_update_vm_power(esxi_nodename:str, machine_id: int, request: Request):
    uniq_id = f"{esxi_nodename}|{machine_id}"
    # Parse Request
    req_data = request.get_data()
    req_txt = req_data.decode('utf-8')
    payload = json.loads(req_txt)
    # Get Request status
    power_state = payload.get('state')
    # Change status
    result = connect.app_set_power(uniq_id, power_state)
    return {"status": "ok", "detail": result}
