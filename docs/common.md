# Common Installation Steps

(1) Enable ssh on ESXi Node

[How to Enable SSH on VMware ESXi | phoenixNAP KB](https://phoenixnap.com/kb/esxi-enable-ssh)

(2) Downloads source code

```
cd /opt/
git clone git@github.com:cdsl-research/ecoman.git
cd ecoman
```

(3) Generate a key-pair for ssh

Generate a key-pair (private key and public key) on your laptop

```
mkdir ssh_keys
cd ssh_keys
ssh-keygen -t rsa -b 4096 -f id_rsa
cd ..
```

(4) Regist a public key (id_rsa.pub) to ESXi Node

```
scp ./ssh/id_rsa.pub esxi-node:/etc/ssh/keys-root/authorized_keys
```

Testing ssh with public key:

```
ssh -i ./ssh/id_rsa -l USERNAME esxi-node
```

(5) Create config file 'hosts.yml'

The format is shown in 'Optional Parameters' section in README.

```
vim hosts.yml
```