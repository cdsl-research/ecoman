# Usage

## ECoMan

Create namespace

```
kubectl create namespace ecoman-production
kubectl config set-context --current --namespace=ecoman-production
```

Set slack secret hooks

```
kubectl create secret generic ecoman-secret-vars --from-literal=slack-webhook=https://xxx

# On update
kubectl create secret generic ecoman-secret-vars --from-literal=slack-webhook="https://xxx" --dry-run -o yaml | kubectl apply -f -
```

Set hosts info 

```
kubectl create secret generic ecoman-secret-config --from-file=../hosts.yaml
```

Deploy ecoman

```
kubectl apply -f ecoman.yaml
```

## OAuth2-Proxy

Create secret

```
kubectl create secret generic oauth2-secret-config --from-file=oauth2-proxy.cfg
```

Deploy app

```
kubectl apply -f oauth2-proxy.yaml
```

