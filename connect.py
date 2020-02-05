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
    return {hostname+vm['id']: vm for vm in vmlist}


def esxi():
    import yaml
    with open("hosts.yaml") as f:
        hosts = yaml.safe_load(f.read())

    vm_formated_info = {}
    for host,param in hosts.items():
        client.connect(
            hostname=param.get('hostname'),
            username=param.get('username'),
            password=param.get('password')
        )
        tmp = _get_vm_list(host)
        vm_formated_info.update(_bind_uniq_vmid(tmp, host))
        client.close()
    
    return vm_formated_info


def main():
    result = esxi()
    for r,s in result.items():
        print(r, s)


if __name__ == '__main__':
    main()

