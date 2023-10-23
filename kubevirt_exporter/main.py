import time
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
import kubevirt_api
import ast
import logging

class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        # Get nodes information and get local node services list from response

        response = kubevirt_api.run()
        if response:
            items = response.get('items')
            for item in items:
                if item.get('metadata'):
                    metadata = item.get('metadata')
                    label_key_list =[]
                    label_value_list=[]
                    virtual_machine_name = metadata.get('name')
                    virtual_machine_namespace = metadata.get('namespace')
                    virtual_machine_labels = metadata.get('labels')
                    for label in virtual_machine_labels:
                        if label == 'kubevirt.io/nodeName':
                            label_key_list.append('nodeName')
                        elif label == 'kubevirt.io/domain':
                            label_key_list.append('domain')
                        else:
                            label_key_list.append(label)
                        label_value_list.append(virtual_machine_labels.get(label))
                    label_key_list.append('vm_name')
                    label_key_list.append('vm_namespace')
                    metric2 = GaugeMetricFamily('kubevirt_virtual_machine_labels', 'Labels of Virtual Machine',
                                                labels=label_key_list)
                    virtual_machine_mfields = metadata.get('managed_fields')
                    fields = virtual_machine_mfields[0]
                    time = fields.get('time')
                if 'status' in item:
                    status = item.get('status')
                    interfaces = status.get('interfaces')
                    ip_address = interfaces[0].get('ip_address')
                    phase = status.get('phase')
                    node_name = status.get('node_name')
                    metric1 = GaugeMetricFamily('kubevirt_virtual_machine_status', 'Status Of Virtual Machine',
                                                labels=['vm_name', 'vm_namespace', 'vm_ip_address', 'node_name', 'vm_phase',
                                                        'startedAt'])
                    if phase == "Running":
                        status_value = 1
                    else:
                        status_value = 0
                    label_value_list.append(virtual_machine_name)
                    label_value_list.append(virtual_machine_namespace)
                    metric1.add_metric(
                        [virtual_machine_name, virtual_machine_namespace, ip_address, node_name, phase, time],
                        status_value)
                    metric2.add_metric(label_value_list,status_value)
                    yield metric2
                    yield metric1
        else:
            logging.info('There is no deployed virtual machine')


if __name__ == '__main__':
    start_http_server(9999)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(5)
