# ECoMan

ECoMan is a tool for supporting virtual machine management on VMware ESXi.
It provides administrators to view virtual machine lists with web user interface.

<img src="demo.gif" width="600">

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

## Getting Started

ECoMan has several ways for running as below.

- Linux Machine (General)
- Docker Compose (Easy)
- Kubernetes

### Linux Machine

TBD

### Docker Compose

TBD

### Kubernetes

TBD

## Optional Parameters

Environment Variables:

| Name                           | Default Value | Type    | Description | Component |
| ---                            | ---           | ---     | ---         | crawler, dashboard |
| MONGO_USERNAME                 |               | String  | If this value is empty, ECoMan connects to MongoDB without authentication. | crawler |
| MONGO_PASSWORD                 |               | String  |             | crawler, dashboard |
| MONGO_DBNAME                   | ecoman        | String  |             | crawler, dashboard |
| MONGO_HOST                     | 127.0.0.1     | String  |             | crawler, dashboard |
| CRAWLER_INTERVAL               | 60            | Integer |             | crawler |
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

<img src="architecture.png">