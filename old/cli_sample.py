import crawler.connecter as connecter

for i in range(42, 81):
    x = connecter.api_create_vm({
        'name': f"koyama-log{i:03d}",
        'ram': 1024,
        'esxi_node': "rose",
        'cpu': 1,
        'storage': 30
    })
    print(x)
