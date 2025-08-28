import json
import subprocess
from pathlib import Path

from monitoring_installation import YAMLwriter, GPU


def store_char_agent_envs(gpu_list):
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
            with env_path.open("a") as f:
                if vendor or model:
                    f.write(f"DEVICE_MODEL={model}\n")
                    f.write(f"GPU_LIST={gpu_list}\n")

def find_architecture():
    with open('nodeInfo.json') as json_file:
        data = json.load(json_file)
        arch = data.get('architecture')
    return arch

arch = find_architecture()
gpu_list = GPU.info()
if arch == "x86_64":
    store_char_agent_envs(gpu_list)