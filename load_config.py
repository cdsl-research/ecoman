from dataclasses import dataclass
import os
import pathlib

import yaml


@dataclass
class HostsConfig:
    addr: str
    username: str
    password: str
    datastore_path: pathlib.Path
    installer_iso_path: pathlib.Path


def get_esxi_nodes():
    """ ESXi一覧をファイルから取得 """

    if os.environ.get('HOSTS_PATH'):
        HOSTS_PATH = str(os.environ.get('HOSTS_PATH'))
    else:
        HOSTS_PATH = "hosts.yml"

    with open(HOSTS_PATH) as f:
        hosts_config = yaml.safe_load(f.read())

    for esxi_nodename, conf in hosts_config.items():
        print("Validating:", esxi_nodename)
        try:
            HostsConfig(**conf)
        except Exception as e:
            print("Fail to validate:", HOSTS_PATH)
            raise e


if __name__ == "__main__":
    get_esxi_nodes()
