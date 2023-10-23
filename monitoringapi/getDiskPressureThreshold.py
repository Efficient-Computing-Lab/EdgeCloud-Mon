##--------------------------------------------------
#
# Get the value of imageGCHighThresholdPercent on master node using KubeVirt REST API
#
# using the shell I can do:
#    $ curl -sSL "http://localhost:8001/api/v1/nodes/${NODE_NAME}/proxy/configz" | jq '.kubeletconfig|.kind="KubeletConfiguration"|.apiVersion="kubelet.config.k8s.io/v1beta1"' | jq .imageGCHighThresholdPercent
#
# Author:	Lorenzo Blasi
# Created:	29/9/2022
#
# © Copyright 2022 Hewlett Packard Enterprise Development LP
# --------------------------------------------------

import sys
import os
import yaml
#
# To install the Kubernetes Python Client SDK:
#    $ sudo apt install git
#    $ pip3 install git+https://github.com/kubernetes-client/python.git
#
from kubernetes import client, config
from kubernetes.client.rest import ApiException
#
# To print the traceback in exceptions
#
import traceback

#
# --------
#
k8s_client = None


#
# --------------------------------------------------
# Utility functions
#
def get_master_node_name():
    try:
        node_list = client.CoreV1Api().list_node()
    except ApiException as e:
        print(f'Exception when calling CoreV1Api().list_node(): {e}\n')
        sys.exit()
    except:
        # sys.exc_info()[0] contains the error type, i.e. a class inheriting from Exception
        # sys.exc_info()[1] contains an object of that class
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f'Unexpected error: {exc_type} {exc_value}')
        formatted_exc = traceback.format_exc()
        print(f'{formatted_exc}')
        sys.exit()
    # look for master node and get its name
    for node in node_list.items:
        if node.metadata.labels['node-role.kubernetes.io/master'] == 'true':
            return node.metadata.name


def get_disk_pressure_threshold():
    header_params = {}
    header_params['Accept'] = k8s_client.select_header_accept(
        ['application/json', 'application/yaml', 'application/vnd.kubernetes.protobuf'])
    auth_settings = ['BearerToken']
    nodename = get_master_node_name()
    rest_path = f"/api/v1/nodes/{nodename}/proxy/configz"
    try:
        # as response_type I usa the generic "object" which returns a tuple with interesting data as its first item
        proxycfg = k8s_client.call_api(rest_path, "GET",
                                       header_params=header_params,
                                       response_type="object",
                                       auth_settings=auth_settings)
    except ApiException as e:
        print(f'Exception when calling call_api({rest_path}, "GET"): {e}\n')
    except:
        # sys.exc_info()[0] contains the error type, i.e. a class inheriting from Exception
        # sys.exc_info()[1] contains an object of that class
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f'Unexpected error: {exc_type} {exc_value}')
        formatted_exc = traceback.format_exc()
        print(f'{formatted_exc}')
    # unpack data from the resultig tuple
    data, *otherinfo = proxycfg
    # extract and return only the needed data
    return data['kubeletconfig']['imageGCHighThresholdPercent']


# User executing the program must have a valid ~/.kube/config or use env variable KUBECONFIG
def k8s_init():
    global k8s_client
    endpoint = os.getenv("MASTER_IP", "127.0.0.1")
    kubeconfig = os.path.expanduser("/root/k3s.yaml")
    with open("/root/k3s.yaml", 'r') as file:
        try:
            loaded = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    cluster = loaded['clusters'][0]
    cluster_config = cluster.get('cluster')
    cluster_config['server'] = 'https://' + endpoint + ':6443'
    with open("/root/k3s.yaml", 'w') as file:
        try:
            yaml.dump(loaded, file, default_flow_style=False)
        except yaml.YAMLError as exc:
            print(exc)
    config.load_kube_config(config_file=kubeconfig)
    k8s_client = client.ApiClient()

##------------------
