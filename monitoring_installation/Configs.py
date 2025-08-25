import grp
import json
import os
import pwd
import secrets
import signal
import socket
import string
import subprocess
import time
from pathlib import Path

import GPU
import YAMLwriter
import KubernetesInfo

def store_char_agent_envs():
    env_file = "../char_agent/.env"
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
            #env_path = Path(env_file)
            #with env_path.open("a") as f:
            #    if vendor or model:
            #        f.write(f"DEVICE_MODEL={model}\n")
    return model
def find_arch():
    arch = subprocess.Popen(["uname -m"], shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
    arch_out, arch_err = arch.communicate()
    arch = arch_out.decode('utf8')
    return arch.strip()

def kubevirt_question():
    answer = input("Is Kubevirt installed in the Kubernetes cluster? (Y/N)")
    flag_answer = False
    if any(answer.lower() == f for f in ["yes", 'y', '1', 'ye']):
        flag_answer = True
    elif any(answer.lower() == f for f in ['no', 'n', '0']):
        flag_answer = False
    return flag_answer

def kernel_question():
    answer = input("Is the kernel version of this Linux host '5.4.0-117-generic' or higher? (Y/N)")
    flag_answer = False
    if any(answer.lower() == f for f in ["yes", 'y', '1', 'ye']):
        flag_answer = True
    elif any(answer.lower() == f for f in ['no', 'n', '0']):
        flag_answer = False
    return flag_answer

def ACCORDION_question():
    answer = input("Is this installation happening on the ACCORDION Platform? (Y/N)")
    flag_answer = False
    if any(answer.lower() == f for f in ["yes", 'y', '1', 'ye']):
        flag_answer = True
    elif any(answer.lower() == f for f in ['no', 'n', '0']):
        flag_answer = False
    return flag_answer


def find_architecture():
    with open('nodeInfo.json') as json_file:
        data = json.load(json_file)
        arch = data.get('architecture')
    return arch

def find_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        master_ip = s.getsockname()[0]
    except Exception:
        master_ip = '127.0.0.1'
    finally:
        s.close()
    print(master_ip)
    return master_ip


def workers(names):
    for name in names:
        print(name)
        subprocess.call(['kubectl label node ' + name + ' node-role.kubernetes.io/worker=worker'], shell=True)


answer1 = kernel_question()
if answer1:
    arch = find_architecture()
    master_ip = find_ip()
    YAMLwriter.prometheus_kubeControllerManager_DiscoveryEndpoints(master_ip)
    YAMLwriter.prometheus_kubeControllerScheduler_DiscoveryEndpoints(master_ip)
    nodelist = KubernetesInfo.get_info()
    # subprocess.call(['kubectl apply -f prometheus-loadbalancer.yaml'], shell=True)
    # subprocess.call(['kubectl apply -f grafana-loadbalancer.yaml'], shell=True)
    subprocess.call(['sh', './kubectl.sh'])

    subprocess.call(['sh', './get_k3s.sh'])
    gpu_list = GPU.info()
    print(str(gpu_list))

    arch = find_arch()
    print(arch)
    if arch == "x86_64":
        model = store_char_agent_envs()
        YAMLwriter.characterization_agent(gpu_list,model)
    else:
        YAMLwriter.characterization_agent(gpu_list)
    subprocess.call(['kubectl apply -f manifests/characterization-agent'], shell=True)
    subprocess.call(['kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=char-agent'],
                    shell=True)
    subprocess.call(['kubectl apply -f manifests/kube-state-metrics'],shell=True)
    subprocess.call(['kubectl apply -f manifests/node-exporter'],shell=True)
    kubevirt_answer = kubevirt_question()
    if kubevirt_answer:
        YAMLwriter.kubevirt_exporter(master_ip)
        subprocess.call(['kubectl apply -f manifests/kubevirt-exporter'], shell=True)
        subprocess.call(['kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=kubevirt-exporter'],
                        shell=True)
        subprocess.call(['kubectl apply -f manifests/windows-exporter'],shell=True)

    answer2 = ACCORDION_question()
    if answer2:
        rid_ip = KubernetesInfo.get_rid_ip()
        echoserver_ip = KubernetesInfo.get_echoserver_ip()
        minicloud_id = KubernetesInfo.get_id()

        subprocess.call(['kubectl apply -f manifests/option/prometheus-accordion-rules.yaml'], shell=True)
        subprocess.call(['kubectl apply -f manifests/prometheus'], shell=True)
        prometheus_ip = KubernetesInfo.get_service_ip("prometheus-k8s")
        YAMLwriter.monitoring_api(echoserver_ip, rid_ip, prometheus_ip, master_ip, minicloud_id)
        subprocess.call(['kubectl apply -f monitoringAPI-Deployment.yaml'], shell=True)
        subprocess.call(['kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=monitoring-api'],
                    shell=True)
    if not answer2:
        subprocess.call(['kubectl apply -f manifests/option/prometheus-rules.yaml'], shell=True)
        subprocess.call(['kubectl apply -f manifests/prometheus'],shell=True)
if not answer1:
    print("Update the kernel and retry the installation process")
