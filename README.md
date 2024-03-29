# ECoMan

ECoMan is a tool for supporting virtual machine management on VMware ESXi.
It provides administrators to view virtual machine lists with web user interface.

<img src="assets/demo.gif">

## Feature

- View virtual machine lists over multiple ESXi Nodes
- Create a virtual machine via Web UI
- Set power status via Web UI
- Emphasize several machines which have large hardware resources in Web UI

## Requirements

- Python 3.9 or later
    - Paramiko
    - FastAPI
    - PyMongo
- MongoDB 5.0 or later

## Installation

ECoMan has several ways for running as below.

- [Linux Machine (General)](docs/install_linux_machine.md)
- [Kubernetes](docs/install_kubernetes.md)

## Optional Parameters

Hosts config file `hosts.yml` for ESXi Nodes:

```
hoge:  # ESXi Node Name
  addr: 'hoge.a910.tak-cslab.org'  # ESXi Node Address
  username: 'root'  # ESXi Username
  identity_file_path: "ssh/id_rsa"  # SSH Private Key File
  datastore_path: '/vmfs/volumes/datastore1/'  # VM stored path on ESXi
  installer_iso_path: "/vmfs/volumes/datastore1/os-images/ubuntu2004.iso"  # Installer ISO stored path
  network_port_group: "Management Network"  # VM network port group
```

Environment Variables:

| Name                           | Default Value | Type    | Description | Component |
| ---                            | ---           | ---     | ---         | ---       |
| HOSTS_PATH                     | `$PROJECT_ROOT/hosts.yml` | String |  | crawler, dashboard, executor |
| MONGO_USERNAME                 |               | String  | If this value is empty, ECoMan connects to MongoDB without authentication. | crawler, dashboard |
| MONGO_PASSWORD                 |               | String  |             | crawler, dashboard |
| MONGO_DBNAME                   | ecoman        | String  |             | crawler, dashboard |
| MONGO_HOST                     | 127.0.0.1     | String  |             | crawler, dashboard |
| CRAWLER_INTERVAL               | 60            | Integer |             | crawler   |
| DASHBOARD_THRESHOLD_CPU        | 5             | Integer | CPU usage on VM lists is emphasized by this value. | dashboard |
| DASHBOARD_THRESHOLD_RAM_MB     | 8192          | Integer | RAM usage on VM lists is emphasized by this value. | dashboard |
| DASHBOARD_THRESHOLD_STORAGE_GB | 50            | Integer | Storage usage on VM lists is emphasized by this value. | dashboard |
| EXECUTOR_ADDRESS               | 127.0.0.1     | String  |             | dashboard |
| EXECUTOR_PORT                  | 8600          | Integer |             | dashboard, executor |

## Architecture

ECoMan has following system archtiecture.

- `crawler` fetches VMs info via SSH and regist VMs info to MongoDB. This component works by polling.
- `dashboard` provides Web UI to Administrators. When Administrator accesses `dashboard`, it fetches VMs info from MongoDB and returns to Administrator.
- `executor` receives actions, "Create VM" or "Update VM's power", from `dashboard` and does the actions via SSH.

<img src="assets/architecture.png">
