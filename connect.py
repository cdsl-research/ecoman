import paramiko
import asyncio


""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()

machines = []

""" VMのリストを取得 """
def get_vms_list():
    # VM情報一覧の2行目～を取得(ラベルを除外)
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/getallvms')
    vm_info = [line.strip('\n').split() for line in stdout][1:]

    return [{
        'uniq_id':dat[0],
        # 'physical_host': esxi_hostname,
        'id': dat[0],
        'name': dat[1],
        'datastore': dat[2],
        'datastore_path': dat[3],
        'guest_os': dat[4],
        'vm_version': dat[5],
        'comment': ' '.join(dat[6:]),
    } for dat in vm_info]
    

""" VMの電源状態の一覧を取得 """
def get_vms_power():
    # VMの電源一覧を取得
    stdin, stdout, stderr = client.exec_command("""
    for id in `vim-cmd vmsvc/getallvms | sed '/^Vmid.*$/d' | awk '{print $1}'`
    do
      echo -n $id/
      vim-cmd vmsvc/power.getstate $id | grep -v Retrieved
    done
    """)

    # VMの電源一覧を整形
    result = {}
    for line in stdout.readlines():
        vmid, state = line.split('/')
        if 'Suspended' in state:
            result[vmid] = 'suspend'
        elif 'Powered on' in state:
            result[vmid] = 'on'
        elif 'Powered off' in state:
            result[vmid] = 'off'
        else:
            result[vmid] = 'unknown'

    return result


def _get_esxi_hosts():
    import yaml
    with open("hosts.yaml") as f:
        return yaml.safe_load(f.read())


# def set_vm_power(state, my_vmid):
#     assert state in ('on', 'off'), "Power state is not in ('on', 'off')"
#     esxi_hostname, vmid = my_vmid.split('|')
#     # get esxi hosts
#     esxi_hosts = _get_esxi_hosts()
#     # connect target esxi host
#     host = esxi_hosts.get(esxi_hostname)
#     client.connect(
#         hostname=host.get('hostname'),
#         username=host.get('username'),
#         password=host.get('password')
#     )
#     stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/power.{state} {vmid}')
#     client.close()
#     return stdout


def init_vm():
    vm_formated_info = []
    for host,param in _get_esxi_hosts().items():
        # VMにSSH接続
        client.connect(
            hostname=param.get('hostname'),
            username=param.get('username'),
            password=param.get('password')
        )
        # VM一覧を取得
        result = get_vms_list()
        vm_formated_info.append(result)
    
    return vm_formated_info


def main():
    result = init_vm()
    for esx in result:
        for p in esx:
            print(p)


if __name__ == '__main__':
    main()

