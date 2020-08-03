# Usage

Set slack secret hooks

```
kubectl create secret ecoman-secret-vars --from-literal=slack-webhook=https://xxx
```

Set hosts info 

```
kubectl create secret ecoman-secret-config --from-file=../hosts.yaml
```

Deploy ecoman

```
kubectl apply -f ecoman.yaml
```
