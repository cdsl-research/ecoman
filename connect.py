import paramiko
import asyncio


""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()


""" 個別VMの詳細を取得 """
def get_vm_detail(uniq_id):
    hostname,vmid = uniq_id.split('|')
    hostinfo = _get_esxi_hosts().get(hostname)
    if hostinfo is None:
        return "error"
    client.connect(
        hostname=hostinfo.get('addr'),
        username=hostinfo.get('username'),
        password=hostinfo.get('password')
    )
    stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/get.summary {vmid}')
    # client.close()
    return stdout.read().decode('ascii').replace('\n', '\n')

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

""" ESXi一覧をファイルから取得 """
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


def app_top():
    vm_formated_info = []
    for hostname,param in _get_esxi_hosts().items():
        # VMにSSH接続
        client.connect(
            hostname=param.get('addr'),
            username=param.get('username'),
            password=param.get('password')
        )
        # VM一覧を結合
        vm_list = get_vms_list()
        vm_power = get_vms_power()
        for vm in vm_list:
            vm['uniq_id'] = hostname + '|' + vm.get('id')
            vm['physical_host'] = hostname
            try:
                vm['power'] = vm_power[vm['id']]
            except KeyError:
                vm['power'] = 'error'
        vm_formated_info.extend(vm_list)
    
    return vm_formated_info


def main():
    for a in app_top():
        print(a['uniq_id'])
    pass


if __name__ == '__main__':
    main()

