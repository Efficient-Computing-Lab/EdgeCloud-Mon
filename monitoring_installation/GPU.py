import subprocess
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
