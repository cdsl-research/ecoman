import os

import yaml

import model


def get_esxi_nodes() -> dict[str, model.HostsConfig]:
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

    result: dict[str, model.HostsConfig] = {}
    for esxi_nodename, conf in hosts_config.items():
        print("Validating:", esxi_nodename)
        try:
            result[esxi_nodename] = model.HostsConfig(**conf)
        except Exception as e:
            print("Fail to validate:", HOSTS_PATH)
            raise e

    return result


if __name__ == "__main__":
    get_esxi_nodes()
