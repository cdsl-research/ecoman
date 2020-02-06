import base64
import paramiko


"""
Init ssh connecter
"""
client = paramiko.SSHClient()
client.load_system_host_keys()


def _get_vm_list(hostname):
    machines = []
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/getallvms')
    vm_info = [line.strip('\n').split() for line in stdout]
    del vm_info[0]
    for tmp in vm_info:
        machines.append({
            'physical_host': hostname,
            'id': tmp[0],
            'name': tmp[1],
            'datastore': tmp[2],
            'datastore_path': tmp[3],
            'guest_os': tmp[4],
            'vm_version': tmp[5],
            'comment': ' '.join(tmp[6:])
        })
    return machines


def _bind_uniq_vmid(vmlist, hostname):
    return {hostname+'|'+vm['id']: vm for vm in vmlist}


def _get_esxi_hosts():
    import yaml
    with open("hosts.yaml") as f:
        return yaml.safe_load(f.read())


def set_vm_power(state, my_vmid):
    assert state in ('on', 'off'), "Power state is not in ('on', 'off')"
    esxi_hostname, vmid = my_vmid.split('|')
    # get esxi hosts
    esxi_hosts = _get_esxi_hosts()
    # connect target esxi host
    host = esxi_hosts.get(esxi_hostname)
    client.connect(
        hostname=host.get('hostname'),
        username=host.get('username'),
        password=host.get('password')
    )
    stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/power.{state} {vmid}')
    client.close()
    return stdout


def _get_vm_power(my_vmid):
    esxi_hostname, vmid = my_vmid.split('|')
    # get esxi hosts
    esxi_hosts = _get_esxi_hosts()
    # connect target esxi host
    host = esxi_hosts.get(esxi_hostname)
    client.connect(
        hostname=host.get('hostname'),
        username=host.get('username'),
        password=host.get('password')
    )
    stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/power.getstate {vmid}')
    result = stdout.readlines()

    # client.close()
    if 'Suspended\n' in result:
        return 'suspend'
    elif 'Powered on\n' in result:
        return 'on'
    elif 'Powered off\n' in result:
        return 'off'
    else:
        return 'unknown'
    

def init_vm():
    esxi_hosts = _get_esxi_hosts()
    vm_formated_info = {}
    for host,param in esxi_hosts.items():
        client.connect(
            hostname=param.get('hostname'),
            username=param.get('username'),
            password=param.get('password')
        )
        vmlst = _get_vm_list(host)
        vmdct_format = _bind_uniq_vmid(vmlst, host)
        for my_vmid,vm_info in vmdct_format.items():
            vm_info['power'] = _get_vm_power(my_vmid)
        
        vm_formated_info.update(vmdct_format)
        client.close()
    
    return vm_formated_info


def main():
    result = init_vm()
    for r,s in result.items():
        print(r, s)


if __name__ == '__main__':
    main()

