# Install to Linux Machine

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

The format is shown in 'Optional Parameters' section.

```
vim hosts.yml
```

(6) Run several components with python venv

```
### Setup for crawler
cd crawler/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### Starting crawler
python main.py &
cd ..

### Setup for executor
cd executor/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### Starting executor
python main.py &
cd ..

### Starting dashboard
cd dashboard/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### Setup for dashboard
uvicorn main:app --reload --host 0.0.0.0 &
cd ..
```

(7) Access to `http://YOURHOST:8000`
