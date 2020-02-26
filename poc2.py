import paramiko
from multiprocessing import Process


""" Init ssh connecter """
client = paramiko.SSHClient()
client.load_system_host_keys()


""" ESXi一覧をファイルから取得 """
def get_esxi_hosts():
    import yaml
    with open("hosts.yaml") as f:
        return yaml.safe_load(f.read())


hostinfo = get_esxi_hosts().get('jasmine')
client.connect(
    hostname=hostinfo.get('addr'),
    username=hostinfo.get('username'),
    password=hostinfo.get('password')
)
import sys
vm_name = sys.argv[1]
cmd = f"""
ram=1024
cpu=1
ssd=20G
vm_name={vm_name}
vmid=`vim-cmd vmsvc/createdummyvm $vm_name /vmfs/volumes/StoreNAS-Jasmine/`

cd /vmfs/volumes/StoreNAS-Jasmine/$vm_name

sed -i -e '/^guestOS =/d' $vm_name.vmx
cat << EOF >> $vm_name.vmx
guestOS = "ubuntu-64"
memsize = "$ram"
numvcpus = "$cpu"
ethernet0.addressType = "generated"
ethernet0.generatedAddressOffset = "0"
ethernet0.networkName = "DMZ-Network"
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
sata0:0.fileName = "/vmfs/volumes/StoreNAS-Public/os-images/custom/ubuntu-18.04.4-server-amd64-preseed.20190824.040414.iso"
sata0:0.present = "TRUE"
EOF

rm $vm_name-flat.vmdk  $vm_name.vmdk
vmkfstools --createvirtualdisk $ssd -d thin $vm_name.vmdk

vim-cmd vmsvc/reload $vmid
vim-cmd vmsvc/power.on $vmid
exit
"""
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.readlines())
print(stderr.readlines())
print("Finish")

client.close()
