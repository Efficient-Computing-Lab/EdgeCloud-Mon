#!/bin/bash

set -e  # exit on error

# 1️⃣ Define function to store char-agent envs
store_char_agent_envs() {
    local gpu_list="$1"
    local path="/opt/char-agent"
    local env_file="$path/.env"

    # Create directory if it doesn't exist
    mkdir -p "$path"
    echo "Directory $path is ready."

    # Get hardware vendor and model
    vendor=$(hostnamectl | grep -w 'Hardware Vendor' | awk -F: '{print $2}' | xargs)
    model=$(hostnamectl | grep -w 'Hardware Model' | awk -F: '{print $2}' | xargs)

    if [[ -n "$vendor" && -n "$model" ]]; then
        device_model="$vendor $model"
        echo "$device_model"
        # Write .env file
        echo "DEVICE_MODEL=$device_model" > "$env_file"
        echo "GPU_LIST=$gpu_list" >> "$env_file"
    fi
}

# 2️⃣ Find architecture from nodeInfo.json
arch=$(jq -r '.architecture' nodeInfo.json)
echo "$arch"

# 3️⃣ Get GPU info
# You need a script or command to get GPU info; assuming GPU.sh exists:
gpu_list=$(sh ./gpu.sh)

# 4️⃣ Conditionally store envs
if [[ "$arch" == "x86_64" || "$arch" == "amd64" ]]; then
    store_char_agent_envs "$gpu_list"
fi
