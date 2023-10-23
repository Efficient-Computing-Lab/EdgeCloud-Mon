kubectl delete -f manifests/characterization-agent
kubectl delete -f manifests/kubevirt-exporter
kubectl delete -f manifests/windows-exporter
kubectl delete -f manifests/kube-state-metrics
kubectl delete -f manifests/node-exporter
kubectl delete -f manifests/option
kubectl delete -f manifests/prometheus
kubectl delete -f manifests/setup
kubectl delete -f prometheus-volume.yaml
rm -r /opt/Prometheus