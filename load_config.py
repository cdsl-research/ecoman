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


def get_esxi_nodes():
    """ ESXi一覧をファイルから取得 """

    if os.environ.get('HOSTS_PATH'):
        HOSTS_PATH = str(os.environ.get('HOSTS_PATH'))
    else:
        HOSTS_PATH = "hosts.yml"

    with open(HOSTS_PATH) as f:
        hosts_config = yaml.safe_load(f.read())

    for conf in hosts_config:
