import os
import pathlib
from dataclasses import dataclass

import yaml


@dataclass
class HostsConfig:
    addr: str
    username: str
    identity_file_path: pathlib.Path
    datastore_path: pathlib.Path
    installer_iso_path: pathlib.Path
    network_port_group: str


def get_esxi_nodes() -> dict[str, HostsConfig]:
    """ESXi一覧をファイルから取得
    Return::
        key: esxi node name
        value: esxi node detail
    """

    if os.environ.get("HOSTS_PATH"):
        HOSTS_PATH = str(os.environ.get("HOSTS_PATH"))
    else:
        dir_this_file = os.path.dirname(__file__)
        parent_dir = os.path.join(dir_this_file, "..")
        HOSTS_PATH = os.path.join(parent_dir, "hosts.yml")

    print("Load Config Path:", HOSTS_PATH)
    with open(HOSTS_PATH) as f:
        hosts_config = yaml.safe_load(f.read())

    result: dict[str, HostsConfig] = {}
    for esxi_nodename, conf in hosts_config.items():
        print("Validating:", esxi_nodename)
        try:
            hosts_conf = HostsConfig(**conf)
            hosts_conf.identity_file_path = os.path.join(
                parent_dir, hosts_conf.identity_file_path
            )
            result[esxi_nodename] = hosts_conf
        except Exception as e:
            print("Fail to validate:", HOSTS_PATH)
            raise e

    return result


if __name__ == "__main__":
    get_esxi_nodes()
