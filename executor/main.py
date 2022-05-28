from dataclasses import dataclass
import os
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


# def create_vm(
#     name: str,  # 'ecoman-example3'
#     ram_mb: int,  # 512
#     cpu_cores: int,  # 1
#     storage_gb: int,  # 30
#     network_port_group: str,  # "private"
#     store_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Jasmine/"
#     iso_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Public/xxx.iso"
#     esxi_nodename: str,  # "jasmine"
#     comment: str
# ) -> ProcessResult:
#     """ VMを作成 """

#     hostinfo = load_config.get_esxi_nodes().get(esxi_nodename)
#     client.connect(
#         hostname=hostinfo.get('addr'),
#         username=hostinfo.get('username'),
#         password=hostinfo.get('password')
#     )

#     # dt_now = datetime.datetime.now()
#     # CUR_DATE = dt_now.strftime('%Y-%m-%d %H:%M:%S')

#     concat_payload = comment
#     cmd = f"""
#     vmid=`vim-cmd vmsvc/createdummyvm {name} {store_path}`
#     cd {store_path}{name}
#     sed -i -e '/^guestOS =/d' {name}.vmx

#     cat << EOF >> {name}.vmx
# guestOS = "ubuntu-64"
# memsize = "{ram_mb}"
# numvcpus = "{cpu_cores}"
# ethernet0.addressType = "generated"
# ethernet0.generatedAddressOffset = "0"
# ethernet0.networkName = "{network_port_group}"
# ethernet0.pciSlotNumber = "160"
# ethernet0.present = "TRUE"
# ethernet0.uptCompatibility = "TRUE"
# ethernet0.virtualDev = "vmxnet3"
# ethernet0.wakeOnPcktRcv = "TRUE"
# powerType.powerOff = "default"
# powerType.reset = "default"
# powerType.suspend = "soft"
# sata0.present = "TRUE"
# sata0:0.deviceType = "cdrom-image"
# sata0:0.fileName = "{iso_path}"
# sata0:0.present = "TRUE"
# annotation = "{concat_payload}"
# EOF

#     rm {name}-flat.vmdk  {name}.vmdk
#     vmkfstools --createvirtualdisk {storage_gb}G -d thin {name}.vmdk
#     vim-cmd vmsvc/reload $vmid
#     vim-cmd vmsvc/power.on $vmid
#     """

#     # print(cmd)
#     _, stdout, stderr = client.exec_command(cmd)
#     stdout_lines = stdout.readlines()
#     stderr_lines = stderr.readlines()
#     if len(stderr_lines) > 0:
#         payload = ' '.join([line.strip() for line in stderr_lines])
#         # slack_notify(f"[Error] {author} created {vm_name}. detail: {payload}")
#         return {
#             "result": payload
#         }
#         # return ProcessResult()
#     else:
#         payload = ' '.join([line.strip() for line in stdout_lines])
#         # slack_notify(
#         #     f"[Success] {author} created {vm_name}. detail: {payload}")
#         return {
#             "status": payload
#         }


if __name__ == "__main__":
    """ Init rpc server """
    listen_port = int(os.getenv("EXECUTOR_PORT", "8600"))
    server = SimpleXMLRPCServer(("0.0.0.0", listen_port))
    print(f"Listening on port {listen_port} ...")
    server.register_function(set_vm_power, "set_vm_power")
    server.serve_forever()
