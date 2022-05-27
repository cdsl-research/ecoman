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


def get_esxi_nodes() -> dict[str, HostsConfig]:
    """ ESXi一覧をファイルから取得
    Return::
        key: esxi node name
        value: esxi node detail
    """

    if os.environ.get('HOSTS_PATH'):
        HOSTS_PATH = str(os.environ.get('HOSTS_PATH'))
    else:
        HOSTS_PATH = "hosts.yml"

    with open(HOSTS_PATH) as f:
        hosts_config = yaml.safe_load(f.read())

    result: dict[str, HostsConfig] = {}
    for esxi_nodename, conf in hosts_config.items():
        print("Validating:", esxi_nodename)
        try:
            result[esxi_nodename] = HostsConfig(**conf)
        except Exception as e:
            print("Fail to validate:", HOSTS_PATH)
            raise e

    return result


if __name__ == "__main__":
    get_esxi_nodes()
