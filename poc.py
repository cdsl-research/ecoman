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
cmd = """
ram=1024
cpu=1
vm_name=hoge022
vmid=`vim-cmd vmsvc/createdummyvm $vm_name /vmfs/volumes/StoreNAS-Jasmine/`

cd /vmfs/volumes/StoreNAS-Jasmine/$vm_name
rm $vm_name-flat.vmdk  $vm_name.vmdk
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
EOF

ls -t /vmfs/volumes/StoreNAS-Public/cdsl-master-ubuntu1804/cdsl-master-ubuntu1804-*.vmdk | grep [0-9]\\\\{6\\\\}\\.vmdk | awk '{print $1}' > /tmp/vmpath
echo /vmfs/volumes/StoreNAS-Public/cdsl-master-ubuntu1804/cdsl-master-ubuntu1804.vmdk > /tmp/vmpath
vmkfstools -i `head -n 1 /tmp/vmpath` /vmfs/volumes/StoreNAS-Jasmine/$vm_name/$vm_name.vmdk

vim-cmd vmsvc/reload $vmid
vim-cmd vmsvc/power.on $vmid
exit
"""
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.readlines())
print(stderr.readlines())
print("Finish")

client.close()
