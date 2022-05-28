# class ProcessResult:
#     OK: int = "ok"
#     NG: int = "ng"


# def set_vm_power(_client: paramiko.SSHClient, esxi_nodename: str, vmid: int, power_state: PowerStatus) -> str:
#     """ 個別VMの電源を操作 """

#     esxi_node_info: load_config.HostsConfig = load_config.get_esxi_nodes()[
#         esxi_nodename]
#     assert esxi_node_info is not None, "Undefined uniq_id."
#     POWER_STATE = ('on', 'off', 'shutdown', 'reset', 'reboot', 'suspend')
#     assert power_state in POWER_STATE, "Invalid power state."

#     _client.connect(
#         hostname=esxi_node_info.get('addr'),
#         username=esxi_node_info.get('username'),
#         password=esxi_node_info.get('password')
#     )
#     _, stdout, _ = _client.exec_command(
#         f'vim-cmd vmsvc/power.{power_state} {vmid}')
#     # TODO: 判定を作成
#     '''
#     ON) Powering on VM:
#     SHUTDOWN) 空
#     OFF) Powering off VM:
#     RESET) Reset VM:
#     REBOOT) 空
#     SUSPEND) Suspending VM:
#     '''
#     # client.close()
#     return stdout.read().decode().strip('\n')


# def create_vm(
#     _client: paramiko.SSHClient,
#     name: str,  # 'ecoman-example3'
#     ram_mb: int,  # 512
#     cpu_cores: int,  # 1
#     storage_gb: int,  # 30
#     network_port_group: str,  # "private"
#     store_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Jasmine/"
#     iso_path: pathlib.Path,  # "/vmfs/volumes/StoreNAS-Public/xxx.iso"
#     esxi_nodename: str,  # "jasmine"
#     comment: str
# ) -> ProcessResult:
#     """ VMを作成 """

#     hostinfo = load_config.get_esxi_nodes().get(esxi_nodename)
#     _client.connect(
#         hostname=hostinfo.get('addr'),
#         username=hostinfo.get('username'),
#         password=hostinfo.get('password')
#     )

#     # dt_now = datetime.datetime.now()
#     # CUR_DATE = dt_now.strftime('%Y-%m-%d %H:%M:%S')

#     concat_payload = comment
#     cmd = f"""
#     vmid=`vim-cmd vmsvc/createdummyvm {name} {store_path}`
#     cd {store_path}{name}
#     sed -i -e '/^guestOS =/d' {name}.vmx

#     cat << EOF >> {name}.vmx
# guestOS = "ubuntu-64"
# memsize = "{ram_mb}"
# numvcpus = "{cpu_cores}"
# ethernet0.addressType = "generated"
# ethernet0.generatedAddressOffset = "0"
# ethernet0.networkName = "{network_port_group}"
# ethernet0.pciSlotNumber = "160"
# ethernet0.present = "TRUE"
# ethernet0.uptCompatibility = "TRUE"
# ethernet0.virtualDev = "vmxnet3"
# ethernet0.wakeOnPcktRcv = "TRUE"
# powerType.powerOff = "default"
# powerType.reset = "default"
# powerType.suspend = "soft"
# sata0.present = "TRUE"
# sata0:0.deviceType = "cdrom-image"
# sata0:0.fileName = "{iso_path}"
# sata0:0.present = "TRUE"
# annotation = "{concat_payload}"
# EOF

#     rm {name}-flat.vmdk  {name}.vmdk
#     vmkfstools --createvirtualdisk {storage_gb}G -d thin {name}.vmdk
#     vim-cmd vmsvc/reload $vmid
#     vim-cmd vmsvc/power.on $vmid
#     """

#     # print(cmd)
#     _, stdout, stderr = _client.exec_command(cmd)
#     stdout_lines = stdout.readlines()
#     stderr_lines = stderr.readlines()
#     if len(stderr_lines) > 0:
#         payload = ' '.join([line.strip() for line in stderr_lines])
#         # slack_notify(f"[Error] {author} created {vm_name}. detail: {payload}")
#         return {
#             "result": payload
#         }
#         # return ProcessResult()
#     else:
#         payload = ' '.join([line.strip() for line in stdout_lines])
#         # slack_notify(
#         #     f"[Success] {author} created {vm_name}. detail: {payload}")
#         return {
#             "status": payload
#         }
