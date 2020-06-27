import paramiko
from multiprocessing import Process


client = paramiko.SSHClient()
client.load_system_host_keys()


""" ESXi一覧をファイルから取得 """
def get_esxi_hosts():
    import yaml
    with open("hosts.yaml") as f:
        return yaml.safe_load(f.read())


def create_vm(
        vm_name = 'ecoman-example3',
        vm_ram_mb = 512, 
        vm_cpu = 1, 
        vm_storage_gb = 30, 
        vm_network_name = "private", 
        vm_store_path = "/vmfs/volumes/StoreNAS-Jasmine/",
        vm_iso_path = "/vmfs/volumes/StoreNAS-Public/os-images/custom/ubuntu-18.04.4-server-amd64-preseed.20190824.040414.iso",
        esxi_node_name = "jasmine"
    ):

    hostinfo = get_esxi_hosts().get(esxi_node_name)
    client.connect(
        hostname=hostinfo.get('addr'),
        username=hostinfo.get('username'),
        password=hostinfo.get('password')
    )

    # catコマンドのインデントは変えると動かなくなる
    cmd = f"""
    vmid=`vim-cmd vmsvc/createdummyvm {vm_name} {vm_store_path}`
    cd /vmfs/volumes/StoreNAS-Jasmine/{vm_name}
    
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
EOF

    rm {vm_name}-flat.vmdk  {vm_name}.vmdk
    vmkfstools --createvirtualdisk {vm_storage_gb}G -d thin {vm_name}.vmdk
    
    vim-cmd vmsvc/reload $vmid
    vim-cmd vmsvc/power.on $vmid
    exit
    """
    # print(cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout, stderr

sout, serr = create_vm(vm_name="hoge12")
print(sout.readlines())
print(serr.readlines())

client.close()
