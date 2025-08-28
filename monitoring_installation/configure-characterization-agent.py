import json
import subprocess
from pathlib import Path
import os
import re
from collections import defaultdict


def info():
    found = False
    gpu_list = []
    gpu_info = subprocess.Popen(["lspci -v | grep -A 10 -E 'VGA compatible controller'"], shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = gpu_info.communicate()
    lines = out.decode('ascii')
    lines = lines.splitlines()
    number_of_lines = len(lines)
    line_number = 0
    memory_counter = 0
    gpu_json = {}
    for l in lines:
        line_number = line_number + 1
        lre = re.sub(r"^\s+", "", l)
        if 'VGA compatible controller' in lre:
            gpu_device = lre
            if gpu_device:
                found = True
            GPU_device = gpu_device.split('VGA compatible controller: ', 1)[1]
            gpu_json = {"GPU_name": GPU_device}
            gpu_list.append(gpu_json)
    gpu_info.terminate()
    if found:
        # count gpus
        d = defaultdict(int)
        for dic in gpu_list:
            key = dic['GPU_name']
            d[key] += 1
        gpu_list = [i for n, i in enumerate(gpu_list) if i not in gpu_list[n + 1:]]
        id = 0
        for gpu in gpu_list:
            id = id + 1
            gpu["id"] = id
            x = d.items()
            for item in x:
                if gpu.get("GPU_name") == item[0]:
                    gpu["quantity"] = item[1]
    return gpu_list

def store_char_agent_envs(gpu_list):
    path = "/opt/char-agent"
    os.makedirs(path, exist_ok=True)
    print(f"Directory {path} is ready.")
    env_file = "/opt/char-agent/.env"
    vendor_info = subprocess.Popen(["hostnamectl | grep -w 'Hardware Vendor'"], shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
    vend_out, vend_err = vendor_info.communicate()
    vendor = vend_out.decode('utf8')
    model_info = subprocess.Popen(["hostnamectl | grep -w 'Hardware Model'"], shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
    model_out, model_err = model_info.communicate()
    model = model_out.decode('utf8')
    if vendor or model:
        if "Hardware Vendor" in vendor and "Hardware Model" in model:
            vendor = vendor.replace("Hardware Vendor:", "")
            model = model.replace("Hardware Model:", "")
            model = vendor.strip() +" "+ model.strip()
            print(model)
            env_path = Path(env_file)
            with env_path.open("w") as f:
                if vendor or model:
                    f.write(f"DEVICE_MODEL={model}\n")
                    f.write(f"GPU_LIST={gpu_list}\n")

def find_architecture():
    with open('nodeInfo.json') as json_file:
        data = json.load(json_file)
        arch = data.get('architecture')
    return arch


arch = find_architecture()
print(arch)
gpu_list = info()
if arch == "x86_64" or arch =="amd64":
    store_char_agent_envs(gpu_list)