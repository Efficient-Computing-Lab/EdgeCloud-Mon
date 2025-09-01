
## About
Python scripts that utilize YAML files provided byof <a href="https://github.com/carlosedp/cluster-monitoring" target="_blank">Cluster Monitoring stack for ARM / X86-64 platforms</a> project to automate the deployment of Prometheus in a K3s cluster.
## Installation Procedure
Run `prepare.sh` on the master to create the appropriate folders for the monitoring stack and to install the required python libraries.
### Requirements
```bash
sudo ./prepare.sh
```
### Installation
Configs needs to run on a K3s master to deploy the Prometheus monitoring stack.
```bash
python3 Configs.py
```

For the configuration of the characterization agents the following script should run on every node of the cluster:
```bash
sudo ./configure-characterization-agent.sh
```

If the device is a RPi or an X86 machine then:
```bash
kubectl apply -f manifests/characterization-agent/char-agent-exporter-service.yaml
kubectl apply -f manifests/characterization-agent/char-agent-exporter-servicemonitor.yaml
kubectl apply -f manifests/characterization-agent/char-agentDeployment.yaml
kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=char-agent
```

Alternatively if the device is a Jetson then:
```bash
kubectl apply -f manifests/characterization-agent/char-agent-exporter-service.yaml
kubectl apply -f manifests/characterization-agent/char-agent-exporter-servicemonitor.yaml
kubectl apply -f manifests/characterization-agent/char-agentDeployment-jetson.yaml
kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=char-agent
```
Important: Ensure that you deploy the monitoring on Linux hosts running a kernel version of 5.4.0-117-generic or later. If you plan to install the monitoring stack separately from the ACCORDION platform, make sure to select "N" when asked the question: "Is this installation taking place on the ACCORDION Platform? (Y/N)". Selecting "N" will result in the monitoringAPI not being installed in this scenario.