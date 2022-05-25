import ipaddress
import pathlib
import re
from typing import Dict

import paramiko

import load_config
import model
import vim_cmd_parser

""" Init ssh connecter """
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.load_system_host_keys()


# def slack_notify(message):
#     """ Slack通知 """
#     import requests
#     import os
#     SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
#     if SLACK_WEBHOOK:
#         requests.post(SLACK_WEBHOOK, data=json.dumps({
#             'text': message,  # 投稿するテキスト
#         }))


def get_vms_list() -> Dict[int, model.MachineDetail]:
    """ VMのリストを取得 """

    # VM情報一覧の2行目～を取得(ラベルを除外)
    _, stdout, _ = client.exec_command('vim-cmd vmsvc/getallvms')
    vm_info: Dict[int, model.MachineDetail] = {}
    for line in stdout.readlines():
        # 数字から始まる行
        if re.match(r'^\d+', line):
            dat = line.strip('\n').split()
            vmid = int(dat[0])
            vm_info[vmid] = model.MachineDetail(
                id=vmid,
                name=dat[1],
                datastore=dat[2],
                datastore_path=dat[3],
                guest_os=dat[4],
                vm_version=dat[5],
                comment=' '.join(dat[6:])
            )

        # Vmidから始まる行
        elif line.startswith("Vmid"):
            continue

    return vm_info


def get_vms_power() -> Dict[int, model.PowerStatus]:
    """ VMの電源状態のリストを取得 """

    # VMの電源一覧を取得
    _, stdout, _ = client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/power.getstate $id | grep -v Retrieved | sed "s/^/$id|/g" &
    done
    """)

    # VMの電源一覧を整形
    result: Dict[int, model.PowerStatus] = {}
    for line in stdout.readlines():
        _vmid, state = line.split('|')
        vmid = int(_vmid)
        if 'Suspended' in state:
            result[vmid] = model.PowerStatus.SUSPEND
        elif 'Powered on' in state:
            result[vmid] = model.PowerStatus.ON
        elif 'Powered off' in state:
            result[vmid] = model.PowerStatus.OFF
        else:
            result[vmid] = model.PowerStatus.UNKNOWN

    return result


def get_vms_ip() -> Dict[int, ipaddress.IPv4Address]:
    """ VMのIPアドレスのリストを取得 """

    _, stdout, _ = client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/get.summary $id | grep ipAddress | grep -o \"[0-9a-f:\.]\\+\" | sed "s/\"//g;s/^/$id|/g" &
    done
    """)

    result: Dict[int, ipaddress.IPv4Address] = {}
    for line in stdout.readlines():
        vmid, ipaddr = line.split('|')
        result[int(vmid)] = ipaddress.IPv4Address(ipaddr.strip())

    return result


def get_vm_detail(esxi_nodename: str, vmid: int):
    """ 個別VMの詳細を取得 """

    conf = load_config.get_esxi_nodes()
    esxi_nodenames = tuple(conf.keys())  # get ESXi Node List
    assert esxi_nodename in esxi_nodenames, "Invalid esxi_nodename is specified in param"

    esxi_node_info: model.HostsConfig = conf[esxi_nodename]
    client.connect(
        hostname=esxi_node_info.addr,
        username=esxi_node_info.username,
        password=esxi_node_info.password
    )
    _, stdout, _ = client.exec_command(f'vim-cmd vmsvc/get.summary {vmid}')
    vm_detail = vim_cmd_parser.parser(stdout.read().decode().split('\n'))

    return vm_detail


def set_vm_power(esxi_nodename: str, vmid: int, power_state: model.PowerStatus) -> str:
    """ 個別VMの電源を操作 """

    host = load_config.get_esxi_nodes().get(esxi_nodename)
    assert host is not None, "Undefined uniq_id."
    POWER_STATE = ('on', 'off', 'shutdown', 'reset', 'reboot', 'suspend')
    assert power_state in POWER_STATE, "Invalid power state."

    client.connect(
        hostname=host.get('addr'),
        username=host.get('username'),
        password=host.get('password')
    )
    _, stdout, _ = client.exec_command(
        f'vim-cmd vmsvc/power.{power_state} {vmid}')
    # TODO: 判定を作成
    '''
    ON) Powering on VM:
    SHUTDOWN) 空
    OFF) Powering off VM:
    RESET) Reset VM:
    REBOOT) 空
    SUSPEND) Suspending VM:
    '''
    # client.close()
    return stdout.read().decode().strip('\n')


def create_vm(
    name: str,  # 'ecoman-example3'
    ram_mb: int,  # 512
    cpu_cores: int,  # 1
    storage_gb: int,  # 30
    network_port_group: str,  # "private"
    store_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Jasmine/"
    iso_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Public/xxx.iso"
    esxi_nodename: str,  # "jasmine"
    comment: str
) -> model.ProcessResult:
    """ VMを作成 """

    hostinfo = load_config.get_esxi_nodes().get(esxi_nodename)
    client.connect(
        hostname=hostinfo.get('addr'),
        username=hostinfo.get('username'),
        password=hostinfo.get('password')
    )

    # dt_now = datetime.datetime.now()
    # CUR_DATE = dt_now.strftime('%Y-%m-%d %H:%M:%S')

    concat_payload = comment
    cmd = f"""
    vmid=`vim-cmd vmsvc/createdummyvm {name} {store_path}`
    cd {store_path}{name}
    sed -i -e '/^guestOS =/d' {name}.vmx

    cat << EOF >> {name}.vmx
guestOS = "ubuntu-64"
memsize = "{ram_mb}"
numvcpus = "{cpu_cores}"
ethernet0.addressType = "generated"
ethernet0.generatedAddressOffset = "0"
ethernet0.networkName = "{network_port_group}"
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
sata0:0.fileName = "{iso_path}"
sata0:0.present = "TRUE"
annotation = "{concat_payload}"
EOF

    rm {name}-flat.vmdk  {name}.vmdk
    vmkfstools --createvirtualdisk {storage_gb}G -d thin {name}.vmdk
    vim-cmd vmsvc/reload $vmid
    vim-cmd vmsvc/power.on $vmid
    """

    # print(cmd)
    _, stdout, stderr = client.exec_command(cmd)
    stdout_lines = stdout.readlines()
    stderr_lines = stderr.readlines()
    if len(stderr_lines) > 0:
        payload = ' '.join([line.strip() for line in stderr_lines])
        # slack_notify(f"[Error] {author} created {vm_name}. detail: {payload}")
        return {
            "result": payload
        }
        return model.ProcessResult()
    else:
        payload = ' '.join([line.strip() for line in stdout_lines])
        # slack_notify(
        #     f"[Success] {author} created {vm_name}. detail: {payload}")
        return {"status": payload}


def main():
    pass


if __name__ == '__main__':
    main()
