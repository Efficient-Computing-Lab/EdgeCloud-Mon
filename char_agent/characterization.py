from __future__ import division
import subprocess
from collections import defaultdict
import psutil
import cpuinfo
import platform
import re
import os
from urllib.request import urlopen
import json
from ipify import get_ip
from os import path
import uuid
import logging
import ast
import pandas as pd
import time
logging.basicConfig(level=logging.INFO)


def generate_uuid():
    uuid1 = uuid.uuid1()
    empty = True
    currentpath = os.getcwd()
    print(currentpath)
    home = currentpath + "/uuid.txt"
    if path.exists(home):
        with open(home, "r") as r:
            one_char = r.read(1)
            if one_char:
                empty = False

    if empty == True:
        with open(home, "w") as f:
            f.write(str(uuid1))

    if __name__ == '__main__':
        with open(home, "r") as r:
            print(r.readline())
            print('path: ' + home)


def get_location():
    ip = get_ip()
    data = {}
    url = 'http://ip-api.com/json/' + str(ip)
    try:
        response = urlopen(url)
        data = json.load(response)
        latitude = data.get('lat')
        longtitude = data.get('lon')
        city = data.get('city')
        country = data.get('country')
        code = data.get('countryCode')
        continent = data.get('timezone')
        sep = '/'
        continent_stripped = continent.split(sep, 1)[0]
        data = {"region": {"location": city, "country": country, "continent": continent_stripped, "latitude": latitude,
                           "longitude": longtitude}}
    except:
        data = {"region": {"location": "unknown", "country": "unknown", "continent": "unknown", "latitude": 0,
                           "longitude": 0}}
    logging.info(data)
    return data


def get_disk():
    hdd = psutil.disk_usage('/')
    size = hdd.total
    return size


def get_battery():
    # battery info
    battery_percent = 0
    battery = psutil.sensors_battery()
    if battery == None:
        battery_flag = 0
    else:
        battery_percent = int(battery.percent)
        battery_flag = 1
    return battery_flag, battery_percent


def get_host_type():
    # Class info
    pc = subprocess.Popen(["virt-what"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pc.communicate()
    print(out.decode("utf-8"))
    if out.decode("utf-8") == '' or out.decode("utf-8") == ' ':
        node_class = 'Computer'
    else:
        node_class = 'VM'
    logging.info(node_class)
    return node_class


def get_gpu_model(arch):
    gpu_list = []
    found = False
    # GPU info
    if "arm" not in arch:
        gpu_list = os.getenv("GPU_LIST", "#empty")
        if gpu_list != "#empty":
            gpu_list = ast.literal_eval(gpu_list)
            for gpu in gpu_list:
                if "NVIDIA" in gpu.get("GPU_name"):
                    found = True
                    gpu_name = gpu.get("GPU_name")
                    gpu_name = gpu_name.replace("NVIDIA Corporation", "")
                    gpu_name = re.sub("\(.*?\)", "()", gpu_name)
                    gpu_name = gpu_name.replace("(", "").replace(")", "").replace("[", "").replace("]",
                                                                                                   "").strip().replace(
                        " ", "_")
                    gpu_name = "nvidia.com/" + gpu_name.upper()
                    gpu["GPU_name"] = gpu_name
    if "arm" in arch:
        gpu_info = subprocess.Popen(["cat /proc/cpuinfo | grep -w Hardware"], shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
        out, err = gpu_info.communicate()
        chipset = out.decode('utf8')
        model_info = subprocess.Popen(["cat /proc/cpuinfo | grep -w Model"], shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
        out, err = model_info.communicate()
        model = out.decode('utf8')
        chipset = chipset.replace("Hardware	:", "")
        model = model.replace("Model		:", "")
        if "Rev" in model:
            model = model.replace("Rev", "")
            model = model.replace(".", "")
            model = re.sub(r" ?\d+$", "", model)
        chipset_list = [{"model": "Raspberry Pi Pico", "chipset": "RP2040", "id": 1, "GPU_name": "not available"},
                        {"model": "Raspberry Pi 1 Model A", "chipset": "BCM2835", "GPU_name": "VideoCore IV @ 250 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi 3 Model A+", "chipset": "BCM2837B0",
                         "GPU_name": "VideoCore IV @ 250 MHz", "id": 1
                         },
                        {"model": "Raspberry Pi 1 Model B", "chipset": "BCM2835", "GPU_name": "VideoCore IV @ 250 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi 2 Model B", "chipset": "BCM2836", "GPU_name": "VideoCore IV @ 250 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi 2 Model B v1.2", "chipset": "BCM2837",
                         "GPU_name": "VideoCore IV @ 250 MHz", "id": 1
                         },
                        {"model": "Raspberry Pi 3 Model B", "chipset": "BCM2837", "GPU_name": "VideoCore IV @ 250 MHz",
                         "id": 1, },
                        {"model": "Raspberry Pi 3 Model B+", "chipset": "BCM2837B0",
                         "GPU_name": "VideoCore IV @ 300 MHz", "id": 1
                         },
                        {"model": "Raspberry Pi 4 Model B", "chipset": "BCM2711", "GPU_name": "VideoCore VI @ 500 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi Zero PCB v1.2", "chipset": "BCM2835",
                         "GPU_name": "VideoCore IV @ 300 MHz", "id": 1
                         },
                        {"model": "Raspberry Pi Zero PCB v1.3", "chipset": "BCM2835",
                         "GPU_name": "VideoCore IV @ 300 MHz", "id": 1},
                        {"model": "Raspberry Pi Zero W", "chipset": "BCM2835", "GPU_name": "VideoCore IV @ 300 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi Zero 2 W", "chipset": "BCM2710A1", "GPU_name": "VideoCore IV @ 300 MHz",
                         "id": 1},
                        {"model": "Raspberry Pi 400", "chipset": "BCM2711C0", "GPU_name": "VideoCore IV @ 500 MHz",
                         "id": 1}]
        for device in chipset_list:
            if device.get("model") in model.strip() and device.get("chipset") in chipset.strip():
                found = True
                device_to_remove_model = device
                del device_to_remove_model['model']
                del device_to_remove_model['chipset']
                device_to_remove_model["quantity"] = 1
                gpu_list.append(device_to_remove_model)
        gpu_info.terminate()
        model_info.terminate()
    if found:
        result = {"GPU_list": gpu_list}
    else:
        result = {"GPU_list": []}
    logging.info(result)
    return result


def get_cpu():
    CPUinfo = cpuinfo.get_cpu_info()
    brand = CPUinfo.get('brand_raw')
    CPUarch = platform.machine()
    CPUbits = str(CPUinfo.get('bits'))
    CPUcores = CPUinfo.get('count')
    home = os.getcwd()
    items = os.listdir(home)
    logging.info(items)
    # Define column names
    columns = ["Date","CPU Utilization","Total Power","CPU Power","GPU Power"]
    # Read the CSV file with specified column names
    df = pd.read_csv(home+'/output.csv', header=None, names=columns)
    energy_value = df['CPU Power'].iloc[0]
    cpu = {"CPU": {"model": brand, "Arch": CPUarch, "bits": CPUbits, "cores": CPUcores, "energy_watt": energy_value}}
    logging.info(cpu)
    return cpu


def get_ram():
    ram = psutil.virtual_memory()
    RAM = ram.total
    logging.info(RAM)
    return RAM


def get_os():
    OSname = platform.system()
    OSversion = platform.release()
    if 'VERSIONID' in OSversion:
        OSversion = OSversion.replace('VERSIONID', '')
    os = {"OS": {'OS_name': OSname, 'OS_version': OSversion}}
    logging.info(os)
    return os
