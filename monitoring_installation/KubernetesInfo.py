import json
import os
import re
import subprocess
import time
from Node import Node
import YAMLwriter


def get_id():
    k3s = os.popen("kubectl get configmap -n accordion accordionid -o jsonpath='{.data.ACCORDIONID}'").read()
    print(k3s)
    return k3s


def get_rid_ip():
    k3s = os.popen("kubectl get pod -n rid -l app.kubernetes.io/name=rid -o jsonpath='{.items[0].status.podIP}'").read()
    return k3s


def get_echoserver_ip():
    k3s = os.popen("kubectl get service -n accordion echoserver -o jsonpath='{.status.loadBalancer.ingress[0].ip}'").read()
    return k3s


def get_info():
    k3s = os.popen('kubectl get nodes -o wide').read()
    print(k3s)
    name = []
    role = []
    ip = []
    with open("k3s.txt", "w") as f:
        if " " in k3s:
            k3s = re.sub(' +', ' ', k3s)
            f.write(k3s)
    if os.path.exists('k3s.txt'):
        with open("k3s.txt", "r") as r:
            lines = r.readlines()
            for x in lines:
                name.append(x.split(' ')[0])
                role.append(x.split(' ')[2])
                ip.append(x.split(' ')[5])
    os.remove("k3s.txt")

    role.remove('ROLES')
    name.remove('NAME')
    ip.remove('INTERNAL-IP')
    kube_nodelist = []
    i = 0
    while i < len(name):
        print(i)
        node = Node()
        node.set_hostname(name[i])
        node.set_role(role[i])
        node.set_ip(ip[i])
        kube_nodelist.append(node)
        i = i + 1
    return kube_nodelist


def get_service_ip(service_name):
    subprocess.call(['kubectl wait -n monitoring --for=condition=ready --timeout=60s pod -l app=mongod'], shell=True)
    k3s = subprocess.check_output(["kubectl get -n monitoring service " + service_name + " -o json"],
                                  shell=True).decode(
        "utf-8")
    json_file = json.loads(k3s)
    spec = json_file.get('spec')
    ip = spec.get('clusterIP')
    ports = spec.get('ports')
    for port in ports:
        port_number = port.get('port')
    ip = ip + ":" + str(port_number)
    print(ip)
    return ip
