import paramiko
import asyncio


""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()

machines = []

""" VM一覧に追加 """
def _add_vm_info(dat, esxi_hostname):
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/power.getstate {}'.format(dat[0]))
    result = stdout.readlines()
    # client.close()

    if 'Suspended\n' in result:
        power =  'suspend'
    elif 'Powered on\n' in result:
        power = 'on'
    elif 'Powered off\n' in result:
        power =  'off'
    else:
        power = 'unknown'

    return ({
        'uniq_id': esxi_hostname+'|'+dat[0],
        'physical_host': esxi_hostname,
        'id': dat[0],
        'name': dat[1],
        'datastore': dat[2],
        'datastore_path': dat[3],
        'guest_os': dat[4],
        'vm_version': dat[5],
        'comment': ' '.join(dat[6:]),
        'power': power
    })
    

def _get_vm_list(esxi_hostname):
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/getallvms')
    # VM情報一覧の2行目～を取得(ラベルを除外)
    vm_info = [line.strip('\n').split() for line in stdout][1:]
    # 非同期実行
    cors = [_add_vm_info(vm, esxi_hostname) for vm in vm_info]
    # results = await asyncio.gather(*cors)
    # await loop.run_in_executor(None, time.sleep, sec)
    return cors


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
# 
# 
# async def _get_vm_power(my_vmid):
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
#     stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/power.getstate {vmid}')
#     loop = asyncio.get_event_loop()
#     import time
#     # await loop.run_in_executor(None, time.sleep)
#     await loop.run_in_executor(None, client.exec_command, f'vim-cmd vmsvc/power.getstate {vmid}')
# 
#     result = stdout.readlines()
#     client.close()
# 
#     if 'Suspended\n' in result:
#         return 'suspend'
#     elif 'Powered on\n' in result:
#         return 'on'
#     elif 'Powered off\n' in result:
#         return 'off'
#     else:
#         return 'unknown'


# def _get_vm_power_async(my_vmid_lst):
#     loop = asyncio.get_event_loop()
#     gather = asyncio.gather(
#         *[_get_vm_power(vmid) for vmid in my_vmid_lst]
#     )
#     loop.run_until_complete(gather)


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
        # loop = asyncio.get_event_loop()
        # vmlst = _get_vm_list(param.get('hostname'))
        hostname = param.get('hostname')
        # results = loop.run_until_complete(
        vm_formated_info.append(_get_vm_list(hostname))
        # vmdct_format = _bind_uniq_vmid(vmlst, host)
        # print(results)
        # a = _get_vm_power_async(vmdct_format.keys())
        # print(a)

        # update power status info
        # for my_vmid,vm_info in vmdct_format.items():
        #     vm_info['power'] = _get_vm_power(my_vmid)
        #     # my_vmid を key にしたdictへ _get_vm_power() から代入する？
        
        # vm_formated_info.update(vmdct_format)
        # client.close()
    
    return vm_formated_info


def main():
    result = init_vm()
    for esx in result:
        for vm in esx:
            print(vm['power'])


if __name__ == '__main__':
    main()

