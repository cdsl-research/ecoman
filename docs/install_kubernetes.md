# Install to Kubernetes

You have to read [Common Installation Steps](common.md) before reading this document.

(1) Create a namespace

```
kubectl create namespace ecoman
kubectl config set-context --current --namespace=ecoman
```

(2) Regist ssh private key to secret

Create a secret

```
kubectl create secret generic priv-key --from-file=ssh/id_rsa
```

(3) Create a ConfigMap for hosts.yml

```
kubectl create configmap hosts-config --from-file=hosts.example.yml
```

(4) Apply manifests

```
kubectl apply -f ecoman.yml
```