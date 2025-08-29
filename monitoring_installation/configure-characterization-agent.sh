#!/bin/bash

device_type=$1
# A helper function to get GPU information, mimicking the Python `info()` function.
function get_gpu_info() {
    local gpu_list=""
    local -a gpu_array=()
    local -A gpu_counts

    # Use lspci to find VGA controllers and parse their names.
    # The 'head -n 1' is used because some GPUs show up multiple times in the output.
    while read -r line; do
        if [[ "$line" =~ "VGA compatible controller:" ]]; then
            # Extract the GPU name after the colon.
            gpu_name=$(echo "$line" | sed -E 's/.*VGA compatible controller: (.*)/\1/' | xargs)
            if [[ -n "$gpu_name" ]]; then
                gpu_array+=("$gpu_name")
            fi
        fi
    done < <(lspci -v)

    # Count the occurrences of each unique GPU name.
    for gpu in "${gpu_array[@]}"; do
        ((gpu_counts["$gpu"]++))
    done

    # Create the JSON-like string for the GPU list, which is a key part of the original script.
    local id=0
    for gpu_name in "${!gpu_counts[@]}"; do
        ((id++))
        local count=${gpu_counts["$gpu_name"]}
        # Format the output as a JSON array of objects.
        if [[ -n "$gpu_list" ]]; then
            gpu_list+=","
        fi
        gpu_list+="{\"GPU_name\":\"$gpu_name\",\"id\":$id,\"quantity\":$count}"
    done

    echo "[$gpu_list]"
}

# The function to store environment variables, mimicking `store_char_agent_envs()`.
function store_char_agent_envs() {
    local gpu_list="$1"
    local path="/opt/char-agent"
    local env_file="/opt/char-agent/.env"

    mkdir -p "$path"
    echo "Directory $path is ready."
    if [[ "$arch" == "x86_64" || "$arch" == "amd64" ]]; then
      local vendor_info=$(hostnamectl | grep -w 'Hardware Vendor')
      local model_info=$(hostnamectl | grep -w 'Hardware Model')

      if [[ -n "$vendor_info" && -n "$model_info" ]]; then
          # Extract vendor and model using 'awk' for a cleaner approach.
          local vendor=$(echo "$vendor_info" | awk -F ': ' '{print $2}' | xargs)
          local model_name=$(echo "$model_info" | awk -F ': ' '{print $2}' | xargs)
          local device_model="$vendor $model_name"

          echo "DEVICE_MODEL=$device_model"
          echo "DEVICE_MODEL=$device_model" > "$env_file"
          echo "GPU_LIST=$gpu_list" >> "$env_file"
      fi
    else
        if ["$device_type" == "raspberrypi"]
          device_model=$(grep -w "Model" /proc/cpuinfo 2>/dev/null | awk -F':' '{print $2}' | xargs)
          device_model=${device_model//Model:/}
          device_model=${device_model//Rev/}
          device_model=${device_model//./}
          device_model=$(echo "$device_model" | sed -E 's/ ?[0-9]+$//')
        fi
        if ["$device_type" == "jetson"]
            device_model=$(tr -d '\0' < /proc/device-tree/model)
            device_model=${device_model//Developer Kit/}
        fi

          echo "DEVICE_MODEL=$device_model"
          echo "DEVICE_MODEL=$device_model" > "$env_file"
          echo "GPU_LIST=$gpu_list" >> "$env_file"
    fi
}

# The function to find the system architecture, mimicking `find_architecture()`.
function find_architecture() {
    local arch=""
    if [[ -f "nodeInfo.json" ]]; then
        # Use 'grep' and 'cut' or 'jq' to parse the JSON file.
        # This assumes 'jq' is installed for reliable JSON parsing.
        if command -v jq &> /dev/null; then
            arch=$(jq -r '.architecture' nodeInfo.json)
        else
            # Fallback for systems without 'jq'.
            arch=$(grep -o '"architecture": *"[^"]*"' nodeInfo.json | cut -d'"' -f4)
        fi
    fi
    echo "$arch"
}

# --- Main script execution ---

# Call the function to find the system architecture.
arch=$(find_architecture)
echo "$arch"

# Call the function to get the GPU information.
gpu_list=$(get_gpu_info)

# Check the architecture and proceed if it's x86_64 or amd64.
store_char_agent_envs "$gpu_list"

