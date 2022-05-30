from dataclasses import dataclass
import os
import pathlib
import sys
from xmlrpc.server import SimpleXMLRPCServer

import paramiko

dir_this_file = os.path.dirname(__file__)
parent_dir = os.path.join(dir_this_file, '..')
sys.path.append(parent_dir)

from library import load_config  # noqa


class PowerStatus:
    ON: str = "on"
    OFF: str = "off"
    SUSPEND: str = "suspend"
    UNKNOWN: str = "unknown"


class ProcessResult:
    OK: int = "ok"
    NG: int = "ng"


@dataclass
class ResponseUpdatePowerStatus:
    result: ProcessResult
    request_status: PowerStatus
    message: str


@dataclass
class ResponseCreateMachine:
    result: ProcessResult
    message: str


@dataclass
class CreateMachineSpec:
    name: str
    ram_mb: int
    cpu_cores: int
    storage_gb: int
    network_port_group: str
    esxi_node_name: str
    datastore_path: pathlib.Path
    installer_iso_path: pathlib.Path
    comment: str


EXECUTOR_PORT = int(os.getenv("EXECUTOR_PORT", "8600"))
print("EXECUTOR TARGET:", EXECUTOR_PORT)

""" Init ssh connecter """
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.load_system_host_keys()


def set_vm_power(esxi_node_name: str, vmid: int, power_state: PowerStatus) -> ResponseUpdatePowerStatus:
    """ 個別VMの電源を操作 """

    esxi_node_info = load_config.get_esxi_nodes()[esxi_node_name]
    assert esxi_node_info is not None, "Invalid esxi_node_name."

    client.connect(
        hostname=esxi_node_info.addr,
        username=esxi_node_info.username,
        key_filename=esxi_node_info.identity_file_path,
        timeout=5.0
    )
    _, stdout, stderr = client.exec_command(
        f'vim-cmd vmsvc/power.{power_state} {vmid}')
    ''' stdout example:
    ON) Powering on VM:
    SHUTDOWN) <empty>
    OFF) Powering off VM:
    RESET) Reset VM:
    REBOOT) <empty>
    SUSPEND) Suspending VM:
    '''
    result_err = stderr.read().decode().replace('\n', '')
    result = stdout.read().decode().replace('\n', '')

    if len(result_err) > 0:
        print("Failed", "Err:", result_err)
        response = ResponseUpdatePowerStatus(
            result=ProcessResult.NG,
            request_status=power_state,
            message=result_err
        )
    else:
        print("Success", "Result:", result)
        print("Err:", result_err)
        response = ResponseUpdatePowerStatus(
            result=ProcessResult.OK,
            request_status=power_state,
            message=result
        )

    return response


def create_vm(
    _name: str,  # 'ecoman-example3'
    _ram_mb: int,  # 512
    _cpu_cores: int,  # 1
    _storage_gb: int,  # 30
    _esxi_node_name: str,  # "jasmine"
    _comment: str
) -> ProcessResult:
    """ Create a VM """

    machine: CreateMachineSpec = _validate_machine_req(
        name=_name,
        ram_mb=_ram_mb,
        cpu_cores=_cpu_cores,
        storage_gb=_storage_gb,
        esxi_node_name=_esxi_node_name,
        comment=_comment
    )

    esxi_node_info = load_config.get_esxi_nodes().get(machine.esxi_node_name)
    assert esxi_node_info is not None, "Invalid esxi_node_name."
    print("ESXi Node info:", esxi_node_info)
    datastore_path = esxi_node_info.datastore_path
    assert datastore_path.startswith("/"), "Invalid datastore path"
    datastore_machine_dir = os.path.join(datastore_path, machine.name)
    installer_iso_path = esxi_node_info.installer_iso_path
    assert installer_iso_path.endswith(".iso"), "Invalid installer iso path"

    client.connect(
        hostname=esxi_node_info.addr,
        username=esxi_node_info.username,
        key_filename=esxi_node_info.identity_file_path,
        timeout=5.0
    )

    cmd = f"""
    vmid=`vim-cmd vmsvc/createdummyvm {machine.name} {datastore_path}`
    cd {datastore_machine_dir}
    sed -i -e '/^guestOS =/d' {machine.name}.vmx

    cat << EOF >> {machine.name}.vmx
guestOS = "ubuntu-64"
memsize = "{machine.ram_mb}"
numvcpus = "{machine.cpu_cores}"
ethernet0.addressType = "generated"
ethernet0.generatedAddressOffset = "0"
ethernet0.networkName = "{machine.network_port_group}"
ethernet0.pciSlotNumber = "160"
ethernet0.present = "TRUE"
ethernet0.uptCompatibility = "TRUE"
ethernet0.virtualDev = "vmxnet3"
ethernet0.wakeOnPcktRcv = "TRUE"
powerType.powerOff = "default"
powerType.reset = "default"
powerType.suspend = "soft"
sata0.present = "TRUE"
sata0:0.deviceType = "cdrom-image"
sata0:0.fileName = "{installer_iso_path}"
sata0:0.present = "TRUE"
annotation = "{machine.comment}"
EOF

    rm {machine.name}-flat.vmdk  {machine.name}.vmdk
    vmkfstools --createvirtualdisk {machine.storage_gb}G -d thin {machine.name}.vmdk
    vim-cmd vmsvc/reload $vmid
    vim-cmd vmsvc/power.on $vmid
    """
    # print(cmd)

    _, stdout, stderr = client.exec_command(cmd)
    stdout_lines = stdout.readlines()
    stderr_lines = stderr.readlines()
    if len(stderr_lines) > 0:
        # failed
        result = ' '.join([line.strip() for line in stderr_lines])
        response = ResponseCreateMachine(
            result=ProcessResult.NG, message=result)
    else:
        # success
        result = ' '.join([line.strip() for line in stdout_lines])
        response = ResponseCreateMachine(
            result=ProcessResult.OK, message=result)

    return response


def _validate_machine_req(
    name: str,  # 'ecoman-example3'
    ram_mb: int,  # 512
    cpu_cores: int,  # 1
    storage_gb: int,  # 30
    esxi_node_name: str,  # "jasmine"
    comment: str
) -> CreateMachineSpec:
    """ Validate a VM hardware spec """

    # NAME
    if name:
        name: str = name.lower()
    else:
        import random
        suffix = str(random.randint(0, 999)).zfill(3)
        name = f"machine-{suffix}"

    # RAM
    if 512 <= ram_mb <= 8192:
        ram_mb: int = ram_mb
    else:
        ram_mb = 512

    # CPU
    if 1 <= cpu_cores:
        cpu_cores: int = cpu_cores
    else:
        cpu_cores = 1

    # Storage
    if 30 <= storage_gb <= 100:
        storage_gb: int = storage_gb
    else:
        storage_gb = 30

    conf = load_config.get_esxi_nodes()
    esxi_node_names = tuple(conf.keys())  # get ESXi Node List

    # ESXi Node
    if esxi_node_name in esxi_node_names:
        esxi_node_name: str = esxi_node_name
    else:
        esxi_node_name: str = random.choice(esxi_node_names)

    # Network
    network_port_group: str = conf[esxi_node_name].network_port_group

    # Datastore Path, Installer ISO Path
    esxi_node_config: load_config.HostsConfig = conf[esxi_node_name]
    datastore_path = esxi_node_config.datastore_path
    installer_iso_path = esxi_node_config.installer_iso_path

    return CreateMachineSpec(
        name=name,
        ram_mb=ram_mb,
        cpu_cores=cpu_cores,
        storage_gb=storage_gb,
        network_port_group=network_port_group,
        esxi_node_name=esxi_node_name,
        datastore_path=datastore_path,
        installer_iso_path=installer_iso_path,
        comment=comment
    )


if __name__ == "__main__":
    """ Init rpc server """
    server = SimpleXMLRPCServer(("0.0.0.0", EXECUTOR_PORT))
    print(f"Listening on port {EXECUTOR_PORT} ...")
    server.register_function(set_vm_power, "set_vm_power")
    server.register_function(create_vm, "create_vm")
    server.serve_forever()
