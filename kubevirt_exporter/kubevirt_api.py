import json
import sys
from kubernetes import config
import kubevirt
from kubevirt.rest import ApiException
import os
import yaml
import json
import ast
import threading
exact = "true"  # bool | Should the export be exact. Exact export maintains cluster-specific fields like 'Namespace'. (optional)
export = "true"  # bool | Should this value be exported. Export strips fields that a user can not specify. (optional)


# Initialization function from https://github.com/kubevirt/client-python/blob/master/examples/examplelib.py

def get_client(kubeconfig=None):
    """
    This function loads kubeconfig and return kubevirt.DefaultApi() object.
    Args:
        kubeconfig (str): Path to kubeconfig
    Returns:
        kubevirt.DefaultApi: Instance of KubeVirt client
    """
    endpoint = os.getenv("IP", "127.0.0.1")
    if kubeconfig is None:
        kubeconfig = os.environ.get("KUBECONFIG")
        if kubeconfig is None:
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

    cl = config.kube_config._get_kube_config_loader_for_yaml_file(kubeconfig)
    cl.load_and_set(kubevirt.configuration)
    return kubevirt.DefaultApi()


def run():
    ##------------------ Initialize
    api_instance = get_client()
    api_flag = True
    auth_settings = []
    ##------------------ Directly call the REST API
    # Calling the API we retrieve the object VirtualMachineInstance with the given vmname and in the given namespace
    # The call is documented in http://kubevirt.io/api-reference/v0.38.1/operations.html#_readnamespacedvirtualmachineinstance
    # Result is of type V1VirtualMachineInstance, see https://github.com/kubevirt/client-python/blob/master/docs/V1VirtualMachineInstance.md
    try:
        api_response = api_instance.list_virtual_machine_instance_for_all_namespaces()
    except ApiException as e:
        print("Exception when calling DefaultApi->read_all_virtual_machine_instances: %s\n" % e)
        api_response = ''
        final_format = api_response
        api_flag = False
    if api_flag:
        dict_response = api_response
        nsr = str(dict_response).replace('\n', '')
        double_quote_string = nsr.replace("\'", "\"")
        no_slashes = double_quote_string.replace("\\", "")
        final_format = ast.literal_eval(no_slashes)


    return final_format
