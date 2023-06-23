kubectl delete ns test
kubectl delete service web -n default
kubectl config set-context --current --namespace default
kubectl delete deployment web
