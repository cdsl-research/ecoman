import re
import json
import paramiko

import vim_cmd_parser


""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()


""" ESXi一覧をファイルから取得 """
def get_esxi_hosts():
    import yaml
    with open("hosts.yaml") as f:
        return yaml.safe_load(f.read())


# """ ESXiのhost->addrを解決 """
# def app_resolve_esxi_addr(esxi_host):
#     esxi_dct = get_esxi_hosts()
#     try:
#         esxi_addr = esxi_dct[esxi_host]['addr']
#     except KeyError:
#         raise ValueError("Cloud not resolve host. Given undefined host.")
#     return esxi_addr


""" VMのリストを取得 """
def get_vms_list():
    import re
    import json

    def parse_info_tag(dat):
        vm_memo = re.search(r'<info>.+</info>', dat['comment'], flags=re.DOTALL)
        # <info>xxx</info>を含む
        if vm_memo is not None:
            json_str = vm_memo.group().strip('<info>').strip('</info>').strip('\n')
            # print(json_str)
            dat['memo'] = json.loads(json_str)
            # comment属性の<info>xxx</info>を取り除く
            dat['comment'] = re.sub(r'<info>.*</info>', '', dat['comment'], flags=re.DOTALL)

    # VM情報一覧の2行目～を取得(ラベルを除外)
    stdin, stdout, stderr = client.exec_command('vim-cmd vmsvc/getallvms')
    vm_info = []
    for line in stdout.readlines():
        # 数字から始まる行
        if re.match(r'^\d+', line):
            # 前の要素のcommentを組み立て
            if len(vm_info) > 0:
                parse_info_tag(vm_info[-1])

            dat = line.strip('\n').split()
            vm_info.append({
                'id': dat[0],
                'name': dat[1],
                'datastore': dat[2],
                'datastore_path': dat[3],
                'guest_os': dat[4],
                'vm_version': dat[5],
                'comment': ' '.join(dat[6:]),
                'memo': None
            })

        # Vmidから始まる行
        elif line.startswith("Vmid"):
            continue

        # その他の行(コメント)
        else:
            vm_info[-1]['comment'] += line

    # 末尾の要素の <info> </info> を処理
    parse_info_tag(vm_info[-1])
    return vm_info


""" VMの電源状態のリストを取得 """
def get_vms_power():
    # VMの電源一覧を取得
    _, stdout, stderr = client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/power.getstate $id | grep -v Retrieved | sed "s/^/$id|/g" &
    done
    """)

    # VMの電源一覧を整形
    result = {}
    for line in stdout.readlines():
        vmid, state = line.split('|')
        if 'Suspended' in state:
            result[vmid] = 'suspend'
        elif 'Powered on' in state:
            result[vmid] = 'on'
        elif 'Powered off' in state:
            result[vmid] = 'off'
        else:
            result[vmid] = 'unknown'

    return result


""" VMのIPアドレスのリストを取得 """
def get_vms_ip():
    _, stdout, stderr = client.exec_command(r"""
    for id in `vim-cmd vmsvc/getallvms | grep '^[0-9]\+' | awk '{print $1}'`
    do
      vim-cmd vmsvc/get.summary $id | grep ipAddress | grep -o \"[0-9a-f:\.]\\+\" | sed "s/\"//g;s/^/$id|/g" &
    done
    """)

    result = {}
    for line in stdout.readlines():
        vmid, ipaddr = line.split('|')
        result[vmid] = ipaddr

    return result


""" 個別VMの詳細を取得 """
def get_vm_detail(esxi_hostname, vmid):
    hostinfo = get_esxi_hosts().get(esxi_hostname)
    if hostinfo is None:
        return "error"

    client.connect(
        hostname=hostinfo.get('addr'),
        username=hostinfo.get('username'),
        password=hostinfo.get('password')
    )
    stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/get.summary {vmid}')
    vm_detail = vim_cmd_parser.parser(stdout.read().decode().split('\n'))
    # TODO: vm_detailが空か判定する
    try:
        info_tag = re.search(r'<info>.*</info>', vm_detail['vim.vm.Summary']['config']['annotation'])
    except KeyError:
        info_tag = None
    
    # Don't have json data
    if info_tag is None:
        vm_org_info = dict()
        annotation = '' 
    else:
        json_str = info_tag.group().strip('<info>').strip('</info>')
        vm_org_info = json.loads(json_str)
        annotation = re.sub(r'<info>.*</info>', '', vm_detail['vim.vm.Summary']['config']['annotation'])

    format_func = lambda x: '' if x is None else x
    vm_detail['info'] = {
        'author': format_func(vm_org_info.get('author')),
        'user': format_func(vm_org_info.get('user')),
        'password': format_func(vm_org_info.get('password')),
        'created_at': format_func(vm_org_info.get('created_at')),
        'tag': ', '.join(format_func(vm_org_info.get('tag'))),
        'annotation': format_func(annotation)
    }
    return vm_detail


""" 個別VMの電源を操作 """
def set_vm_power(esxi_hostname, vmid, power_state):
    host = get_esxi_hosts().get(esxi_hostname)
    assert host is not None, "Undefined uniq_id."
    POWER_STATE = ('on', 'off', 'shutdown', 'reset', 'reboot', 'suspend')
    assert power_state in POWER_STATE, "Invalid power state."
    
    client.connect(
        hostname=host.get('addr'),
        username=host.get('username'),
        password=host.get('password')
    )
    stdin, stdout, stderr = client.exec_command(f'vim-cmd vmsvc/power.{power_state} {vmid}')
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


""" VMを作成 """
def create_vm(
        vm_name = 'ecoman-example3',
        vm_ram_mb = 512, 
        vm_cpu = 1, 
        vm_storage_gb = 30, 
        vm_network_name = "private", 
        vm_store_path = "/vmfs/volumes/StoreNAS-Jasmine/",
        vm_iso_path = "/vmfs/volumes/StoreNAS-Public/os-images/custom/ubuntu-18.04.4-server-amd64-preseed.20190824.040414.iso",
        esxi_node_name = "jasmine",
        author = "unknown",
        tags = [],
        comment = ""
    ):

    hostinfo = get_esxi_hosts().get(esxi_node_name)
    client.connect(
        hostname=hostinfo.get('addr'),
        username=hostinfo.get('username'),
        password=hostinfo.get('password')
    )

    USERNAME = "cdsl"
    PASSWORD = "tutcdsl2019"
    CONCAT_TAGS = ', '.join([f"|22{t}|22" for t in tags])

    import datetime
    dt_now = datetime.datetime.now()
    CUR_DATE = dt_now.strftime('%Y-%m-%d %H:%M:%S')

    concat_payload = comment + "|0A<info>|0A{|0A  |22author|22: |22" + author \
            + "|22,|0A  |22user|22: |22" + USERNAME + "|22,|0A  |22password|22: |22" \
            + PASSWORD + "|22,|0A  |22created_at|22: |22" + CUR_DATE + "|22,|0A  " \
            + "|22tag|22: [ " + CONCAT_TAGS + " ]|0A}|0A</info>"
    # print("payload: ", concat_payload)
    # catコマンドのインデントは変えると動かなくなる
    cmd = f"""
    vmid=`vim-cmd vmsvc/createdummyvm {vm_name} {vm_store_path}`
    cd {vm_store_path}{vm_name}
    
    sed -i -e '/^guestOS =/d' {vm_name}.vmx
    cat << EOF >> {vm_name}.vmx
guestOS = "ubuntu-64"
memsize = "{vm_ram_mb}"
numvcpus = "{vm_cpu}"
ethernet0.addressType = "generated"
ethernet0.generatedAddressOffset = "0"
ethernet0.networkName = "{vm_network_name}"
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
sata0:0.fileName = "{vm_iso_path}"
sata0:0.present = "TRUE"
annotation = "{concat_payload}"
EOF

    rm {vm_name}-flat.vmdk  {vm_name}.vmdk
    vmkfstools --createvirtualdisk {vm_storage_gb}G -d thin {vm_name}.vmdk
    
    vim-cmd vmsvc/reload $vmid
    vim-cmd vmsvc/power.on $vmid
    """
    # print(cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout, stderr


def app_top():
    vm_formated_info = []
    for hostname,param in get_esxi_hosts().items():
        try:
            # VMにSSH接続
            client.connect(
                hostname=param.get('addr'),
                username=param.get('username'),
                password=param.get('password')
            )
        except paramiko.ssh_exception.SSHException as e:
            print(e)

        # VM一覧を結合
        vm_list = get_vms_list()
        vm_power = get_vms_power()
        for vm in vm_list:
            vm['uniq_id'] = hostname + '|' + vm.get('id')
            vm['esxi_host'] = hostname
            vm['esxi_addr'] = param.get('addr')
            try:
                vm['power'] = vm_power[vm['id']]
            except KeyError:
                vm['power'] = 'error'
        vm_formated_info.extend(vm_list)
    
    return vm_formated_info


def app_detail(uniq_id):
    hostname,vmid = uniq_id.split('|')
    return get_vm_detail(hostname, vmid)


def app_set_power(uniq_id, power_state):
    hostname, vmid = uniq_id.split('|')
    return set_vm_power(hostname, vmid, power_state)

def api_create_vm(specs):
    # NAME
    if specs.get('name'):
        vm_name = specs.get('name')
    else:
        import random
        vm_name = 'example-'+str(random.randint(100, 999))

    # RAM
    if specs.get('ram') and int(specs.get('ram')) >= 512:
        vm_ram_mb = int(specs.get('ram'))
    else:
        vm_ram_mb = 512

    # CPU
    if specs.get('cpu') and int(specs.get('cpu')) >= 1:
        vm_cpu = int(specs.get('cpu'))
    else:
        vm_cpu = 1

    # Storage
    if specs.get('storage') and int(specs.get('storage')) >= 30:
        vm_storage_gb = int(specs.get('storage'))
    else:
        vm_storage_gb = 30

    # Network
    if specs.get('network') and specs.get('network') in ('private', 'DMZ-Network'):
        vm_network_name = specs.get('network')
    else:
        vm_network_name = "private"

    # ESXi Node
    if specs.get('esxi_node') and specs.get('esxi_node') in ('jasmine', 'mint'):
        esxi_node_name = specs.get('esxi_node')
    else:
        esxi_node_name = "jasmine"

    # StorePath
    store_path_node = str.capitalize(esxi_node_name)
    vm_store_path = f"/vmfs/volumes/StoreNAS-{store_path_node}/"
    # vm_store_path = "/vmfs/volumes/StorePCIe/"

    # ISO Path
    vm_iso_path = "/vmfs/volumes/StoreNAS-Public/os-images/custom/ubuntu-18.04.4-server-amd64-preseed.20190824.040414.iso"

    # Tags
    if specs.get('tags'):
        tags = specs.get('tags')
    else:
        tags = []

    # Comment
    if specs.get('comment') and len(specs.get('comment')) > 0:
        comment = specs.get('comment')
    else:
        comment = ""

    # Author
    if specs.get('author') and len(specs.get('author')) > 3:
        author = specs.get('author')
    else:
        author = "anonymous"

    stdout, stderr = create_vm(vm_name, vm_ram_mb, vm_cpu, vm_storage_gb, 
            vm_network_name, vm_store_path, vm_iso_path, esxi_node_name,
            author, tags, comment)
    stdout_lines = stdout.readlines()
    stderr_lines = stderr.readlines()
    
    if len(stderr_lines) > 0:
        return {"error": ' '.join([line.strip() for line in stderr_lines])}
    else:
        return {"status": ' '.join([line.strip() for line in stdout_lines])}
    

def main():
    pass


if __name__ == '__main__':
    main()

