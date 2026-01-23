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

# 3️⃣ Add labels to master and worker nodes
add_label() {
    echo "🔍 Fetching available Kubernetes nodes..."
    nodes=($(kubectl get nodes -o jsonpath='{.items[*].metadata.name}'))

    if [[ ${#nodes[@]} -eq 0 ]]; then
        echo "❌ No Kubernetes nodes found."
        return 1
    fi

    echo ""
    echo "📋 Available nodes:"
    i=1
    for n in "${nodes[@]}"; do
        echo "  [$i] $n"
        ((i++))
    done
    echo ""

    # Ask the user to pick one
    read -rp "👉 Enter the number of the node to label as monitoringMaster: " choice

    # Validate input
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#nodes[@]} )); then
        echo "❌ Invalid selection."
        return 1
    fi

    master="${nodes[$((choice-1))]}"
    echo "🧩 You selected: $master"

    # Save master node info
    node_json=$(kubectl get node "$master" -o json)
    echo "$node_json" | jq '.status.nodeInfo' > nodeInfo.json
    chmod 444 nodeInfo.json
    echo "📁 Node information saved to nodeInfo.json"

    # Apply label to master
    kubectl label node "$master" monitoringMaster=true --overwrite
    echo "✅ Label 'monitoringMaster=true' applied to node: $master"

    # Apply labels to worker nodes
    echo ""
    echo "🔖 Labeling worker nodes..."
    worker_index=1
    for n in "${nodes[@]}"; do
        if [[ "$n" != "$master" ]]; then
            kubectl label node "$n" worker=$worker_index --overwrite
            echo "✅ Label 'worker=$worker_index' applied to node: $n"
            ((worker_index++))
        fi
    done

    echo ""
    echo "🎉 All nodes labeled successfully!"
}

# 5️⃣ List nodes with their labels as a valid JSON array
list_nodes_json() {
    echo "📦 Listing all nodes with their labels in JSON..."
    kubectl get nodes -o json | jq '[.items[] | {name: .metadata.name, labels: .metadata.labels}]' > nodes_labels.json
    chmod 444 nodes_labels.json
    echo "📁 Saved node labels to nodes_labels.json"
}

# 4️⃣ Run functions
add_label
kubectl create namespace monitoring || true
create_storage_path "/opt"
list_nodes_json
