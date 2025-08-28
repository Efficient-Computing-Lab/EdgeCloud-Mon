import json
import os
import subprocess


cwd = os.getcwd()

subprocess.call(['sudo apt -y install python3-pip'], shell=True)
subprocess.call(['sh', './pip3.sh'])
subprocess.call(['sh', './gpu.sh'])

import YAMLwriter


def create_storage_path(home):
    if not os.path.exists(home + '/Prometheus'):
        os.makedirs(home + '/Prometheus')
    if not os.path.exists(home + '/Prometheus/prometheus/'):
        name = 'prometheus'
        os.chdir(cwd)
        subprocess.call(['chmod +x prometheus-pv.sh'], shell=True)
        subprocess.call(['sh', './prometheus-pv.sh', str(home)])
        subprocess.call(['kubectl apply -f prometheus-volume.yaml'], shell=True)



def add_label():
    master_node = subprocess.check_output(["kubectl get node --selector='node-role.kubernetes.io/master' -o json"],
                                          shell=True)
    my_json = master_node.decode('utf8').replace("'", '"')
    data = json.loads(my_json)
    items = data.get('items')
    name = ''
    for x in items:
        metadata = x.get('metadata')
        labels = metadata.get('labels')
        print(labels)
        status = x.get('status')
        nodeinfo = status.get('nodeInfo')

        with open('nodeInfo.json', 'w') as outfile:
            json.dump(nodeinfo, outfile)
        os.chmod("nodeInfo.json", 444)
        name = labels.get('kubernetes.io/hostname')
    subprocess.call(['kubectl label nodes ' + name + ' monitoringMaster=true'], shell=True)


add_label()


subprocess.call(['kubectl create namespace monitoring'], shell=True)
create_storage_path('/opt')
