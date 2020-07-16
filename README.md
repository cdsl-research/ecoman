# ECoMan - Easy Computer Manager

## How to run

Setup venv

```
python3 -m venv env
. env/bin/activate
pip installl -r requirements.txt
```

Configure esxi-node credentials on hosts.yaml

```
### Example
mint:
  addr: 'mint.a910.tak-cslab.org'
  username: 'root'
  password: 'xxxxxxxxxx'
```

Try to connect ssh on terminal

```
ssh root@mint.a910.tak-cslab.org
```

Starting app

```
python app.py
```

Acceess Web UI

```
http://<your-hostname>:3300/
```

## Option: OAuth2-Proxy support

This app support enable user to SSO(Single Sing-On) with OAuth2-Proxy. 

Example config `oauth2-proxy.cfg` is put that [here](oauth2-proxy.cfg.example).

New endpoint is `http://<your-hostname>:4180/`.

## Screenshot

VM List

<img src="https://raw.githubusercontent.com/cdsl-research/ecoman/master/ecoman1.jpg" width="500">

VM Detail

<img src="https://raw.githubusercontent.com/cdsl-research/ecoman/master/ecoman2.jpg" width="500">

VM Creation

<img src="https://raw.githubusercontent.com/cdsl-research/ecoman/master/ecoman3.jpg" width="500">

## Demo Movie

[Demo Link](https://twitter.com/i/status/1277117890764828673)
