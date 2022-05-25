import pathlib
from dataclasses import dataclass


@dataclass
class MachineDetail:
    """ Detail info for existing virtual machines
    purpose: READ
    """
    id: int
    name: str
    datastore: str
    datastore_path: pathlib.Path
    guest_os: str
    vm_version: str
    comment: str


@dataclass
class CreateMachineSpec:
    """ """
    name: str
    ram_mb: int
    cpu_cores: int
    storage_gb: int
    network_port_group: str
    esxi_nodename: str
    datastore_path: pathlib.Path
    installer_iso_path: pathlib.Path
    comment: str


class ProcessResult:
    OK: int = "ok"
    NG: int = "ng"


@dataclass
class CreateMchineResult:
    status: ProcessResult
    message: str


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


@dataclass
class HostsConfig:
    addr: str
    username: str
    password: str
    datastore_path: pathlib.Path
    installer_iso_path: pathlib.Path
