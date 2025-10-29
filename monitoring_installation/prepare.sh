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

    name="${nodes[$((choice-1))]}"

    echo "🧩 You selected: $name"

    # Get detailed node info
    node_json=$(kubectl get node "$name" -o json)

    # Save nodeInfo.json
    echo "$node_json" | jq '.status.nodeInfo' > nodeInfo.json
    chmod 444 nodeInfo.json
    echo "📁 Node information saved to nodeInfo.json"

    # Apply label
    kubectl label node "$name" monitoringMaster=true --overwrite
    echo "✅ Label 'monitoringMaster=true' applied to node: $name"
}



# 4️⃣ Run functions
add_label
kubectl create namespace monitoring || true
create_storage_path "/opt"
