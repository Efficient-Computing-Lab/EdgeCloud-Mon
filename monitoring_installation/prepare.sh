#!/bin/bash
apt install -y jq
set -e  # exit on error

cwd=$(pwd)


update-pciids

# 2️⃣ Create Prometheus storage path and apply PV
create_storage_path() {
    local home="$1"

    if [ ! -d "$home/Prometheus" ]; then
        mkdir -p "$home/Prometheus"
    fi

    if [ ! -d "$home/Prometheus/prometheus" ]; then
        chmod +x prometheus-pv.sh
        sh ./prometheus-pv.sh "$home"
        kubectl apply -f prometheus-volume.yaml
    fi
}

# 3️⃣ Add label to master node
add_label() {
    # Get master node name
    master_node_json=$(kubectl get node --selector='node-role.kubernetes.io/master' -o json)
    name=$(echo "$master_node_json" | jq -r '.items[0].metadata.labels["kubernetes.io/hostname"]')

    # Save nodeInfo.json
    echo "$master_node_json" | jq '.items[0].status.nodeInfo' > nodeInfo.json
    chmod 444 nodeInfo.json

    # Apply label
    kubectl label nodes "$name" monitoringMaster=true --overwrite
}

# 4️⃣ Run functions
add_label
kubectl create namespace monitoring || true
create_storage_path "/opt"
