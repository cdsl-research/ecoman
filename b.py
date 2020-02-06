import asyncio
import time
import paramiko

""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()
 
# idをもとに電源状態を取りに行く
async def sleeping(sec):
    await asyncio.sleep(sec)
    return sec

""" VM一覧に追加 """
async def _add_vm_info(dat, esxi_hostname):
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/power.getstate {}'.format(dat[0]))
    result = stdout.readlines()
    #client.close()

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


# idを関数へ渡す
async def master(esxi_hostname):
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/getallvms')
    vm_info = [line.strip('\n').split() for line in stdout][1:]

    tasks = [asyncio.create_task(_add_vm_info(vm, esxi_hostname)) for vm in vm_info]
    # tasks = [asyncio.create_task(sleeping(3)) for vm in vm_info]
    result = await asyncio.gather(*tasks)
    return result

 
def main():
    def _get_esxi_hosts():
        import yaml
        with open("hosts.yaml") as f:
            return yaml.safe_load(f.read())
    for host,param in _get_esxi_hosts().items():
        # VMにSSH接続
        client.connect(
            hostname=param.get('hostname'),
            username=param.get('username'),
            password=param.get('password')
        )
        # loop = asyncio.get_event_loop()
        # v = loop.run_until_complete(master( param.get('hostname') ))
        v = asyncio.run(master(param.get('hostname')))
        # print(v)
        for vv in v:
            print(vv['power'])
 
    # print('\n=== 5つ並列的に動かしてみよう')
    # asyncio.gather(*cors)
    # loop.run_until_complete(gather)
 
 
if __name__ == '__main__':
    main()
