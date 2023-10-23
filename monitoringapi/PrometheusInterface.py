import json
import os
from pathlib import Path
from json import dumps, loads
from datetime import datetime
import logging
from kafka import KafkaProducer
from requests.auth import HTTPBasicAuth
from pprint import pprint
from datetime import timezone
import getDiskPressureThreshold
from Kafka_Producer import Producer
import time
import requests

rid_ip = os.getenv("RID_IP", "127.0.0.1")
prometheus_ip = os.getenv("PROMETHEUS_IP", "0.0.0.0:9090")
echoserver_ip = os.getenv("ECHOSERVER_IP", "#ip")
echoserver_ip_gpu = 'http://' + echoserver_ip + ':40100/resources'
RID_ip_metrics = 'http://' + rid_ip + ':9001/push/nodes'
RID_ip_characterization = 'http://' + rid_ip + ':9001/push/characterization'
Prometheus_ip = 'http://' + prometheus_ip
prometheus_query = Prometheus_ip + '/api/v1/query?'
minicloud_id = os.getenv("MINICLOUD_ID", "#MINICLOUD_ID")
init = getDiskPressureThreshold.k8s_init()


def usable_space_calculation(orderlist_filesystem_size, orderlist_filesystem_free, orderlist_filesystem_avail,
                             threshold):
    filesystem = []
    usable_list = []
    for size in orderlist_filesystem_size:
        for free in orderlist_filesystem_free:
            if free.get('node') == size.get('node'):
                used_value = int(size.get('disk_total_size(bytes)')) - int(free.get('disk_free_space(bytes)'))
                filesystem.append({'node': free.get('node'), 'disk_used_space(bytes)': used_value})
    for avail in orderlist_filesystem_avail:
        for node in filesystem:
            if avail.get('node') == node.get('node'):
                node['disk_avail_space(bytes)'] = int(avail.get('disk_avail_space(bytes)'))
    for node in filesystem:
        used = node.get('disk_used_space(bytes)')
        avail = node.get('disk_avail_space(bytes)')
        usable = int(((threshold - 1) * (used + avail) / 100) - used)
        usable_list.append({'node': node.get('node'), 'disk_free_space(bytes)': usable})
    return usable_list


def uuid_addition(list_without_uuid, uuid_list):
    for record in list_without_uuid:
        for record1 in uuid_list:
            if record1.get('node') == record.get('node'):
                record['uuid'] = record1.get('uuid')


def timestamp():
    # obj = TimezoneFinder()
    # result = obj.timezone_at(lng=longtitude, lat=latitude)
    # tz = pytz.timezone(result)
    # now = datetime.now(tz)
    now = datetime.now(timezone.utc)

    ts = datetime.timestamp(now)
    return ts


def virtual_metrics():
    query = '{__name__=~"accordion_max_pod_cpu_values:1m|accordion_max_pod_memory_values:1m|accordion_max_pod_thread_values:1m|accordion_max_pod_receive_bytes_values:1m|accordion_max_pod_transmit_bytes_values:1m|char_node_location"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('Pod metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    pod_cpu_list = []
    pod_memory_list = []
    pod_thread_list = []
    pod_receive_bytes_list = []
    pod_transmit_bytes_list = []
    node_uuid_list = []
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            value = doc.get('value')
            metric_value = value[1]
            report_time = value[0]
            pod = metric.get('pod')
            node = metric.get('node')
            if metric_name == "accordion_max_pod_cpu_values:1m":
                record = {'node': node, 'pod': pod, 'max_pod_cpu_usage(seconds)': metric_value}
                pod_cpu_list.append(record)
            if metric_name == "accordion_max_pod_memory_values:1m":
                record = {'node': node, 'pod': pod, 'max_pod_memory_usage(bytes)': metric_value}
                pod_memory_list.append(record)
            if metric_name == "accordion_max_pod_thread_values:1m":
                record = {'node': node, 'pod': pod, 'max_pod_threads': metric_value}
                pod_thread_list.append(record)
            if metric_name == "accordion_max_pod_receive_bytes_values:1m":
                record = {'node': node, 'max_receive_bandwidth(bytes)': metric_value}
                pod_receive_bytes_list.append(record)
            if metric_name == "accordion_max_pod_transmit_bytes_values:1m":
                record = {'node': node, 'max_transmit_bandwidth(bytes)': metric_value}
                pod_transmit_bytes_list.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_cpu = sorted(pod_cpu_list, key=lambda k: k['pod'])
        orderlist_ram = sorted(pod_memory_list, key=lambda k: k['pod'])
        orderlist_thread = sorted(pod_thread_list, key=lambda k: k['pod'])
        orderlist_receive = sorted(pod_receive_bytes_list, key=lambda k: k['node'])
        orderlist_transmit = sorted(pod_transmit_bytes_list, key=lambda k: k['node'])
        uuid_addition(orderlist_ram, orderlist_uuid)
        uuid_addition(orderlist_cpu, orderlist_uuid)
        uuid_addition(orderlist_thread, orderlist_uuid)
        uuid_addition(orderlist_receive, orderlist_uuid)
        uuid_addition(orderlist_transmit, orderlist_uuid)
        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {"Pod CPU Usage Results": orderlist_cpu,
                                   "Pod Memory Usage Results": orderlist_ram,
                                   "Pod Threads Results": orderlist_thread,
                                   "Pod Receive Bandwidth Results": orderlist_receive,
                                   "Pod Tramsmit Bandwidth Results": orderlist_transmit}}

    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, 'Results': {}}

    log = {"metrics_set": "Pod Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    producer = Producer()
    try:
        producer.send('accordion.monitoring.currentPod', joined_list)
    except:
        logging.info('could not reach Kafka broker')
    response_status.close()


def physical_metrics():
    threshold = getDiskPressureThreshold.get_disk_pressure_threshold()
    log = {"disk_pressure_threshold": threshold, "time": str(timestamp())}
    logging.info(json.dumps(log, indent=1))
    query = '{__name__=~"accordion_node_cpu_rate_usage:1m|accordion_node_memory_avg_usage:1m|accordion_node_disk_read_latency:1m|accordion_node_disk_write_latency:1m|accordion_node_filesystem_percentage_usage:1m|accordion_node_filesystem_size:1m|accordion_node_filesystem_free:1m|accordion_node_filesystem_avail:1m|accordion_node_disk_io_rate:1m|node_memory_MemAvailable_bytes|accordion_avg_node_network_receive_bytes_total|accordion_avg_node_network_transmit_bytes_total|char_node_location"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    node_cpu_list = []
    node_ram_list = []
    node_disk_read_latency = []
    node_disk_write_latency = []
    node_filesystem_usage = []
    node_filesystem_size = []
    node_filesystem_free = []
    node_filesystem_avail = []
    node_disk_io = []
    node_ram_available_bytes_list = []
    node_network_receive_bytes_list = []
    node_network_transmit_bytes_list = []
    node_uuid_list = []
    logging.info('Node Metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']

        for result in results:
            metric_value = result.get('value')
            value = "% .2f" % float(metric_value[1])
            report_time = metric_value[0]
            metric = result.get('metric')
            metric_name = metric.get('__name__')
            hostname = metric.get('instance')
            if metric_name == 'accordion_node_cpu_rate_usage:1m':
                record = {'node': hostname, 'cpu_usage(percentage)': value}
                node_cpu_list.append(record)
            if metric_name == 'accordion_node_memory_avg_usage:1m':
                record = {'node': hostname, 'mem_usage(percentage)': value}
                node_ram_list.append(record)
            if metric_name == 'accordion_node_disk_read_latency:1m' and 'nan' not in value:
                partition = metric.get('device')
                record = {'node': hostname, 'device': partition, 'disk_read_latency(percentage)': value}
                node_disk_read_latency.append(record)
            if metric_name == 'accordion_node_disk_write_latency:1m' and 'nan' not in value:
                partition = metric.get('device')
                record = {'node': hostname, 'device': partition, 'disk_write_latency(percentage)': value}
                node_disk_write_latency.append(record)
            if metric_name == 'accordion_node_filesystem_percentage_usage:1m':
                record = {'node': hostname, 'filesystem_usage(percentage)': value}
                node_filesystem_usage.append(record)
            if metric_name == 'accordion_node_filesystem_size:1m':
                record = {'node': hostname, 'disk_total_size(bytes)': metric_value[1]}
                node_filesystem_size.append(record)
            if metric_name == 'accordion_node_filesystem_free:1m':
                record = {'node': hostname, 'disk_free_space(bytes)': metric_value[1]}
                node_filesystem_free.append(record)
            if metric_name == 'accordion_node_filesystem_avail:1m':
                record = {'node': hostname, 'disk_avail_space(bytes)': metric_value[1]}
                node_filesystem_avail.append(record)
            if metric_name == 'accordion_node_disk_io_rate:1m':
                record = {'node': hostname, 'disk_io_time_spent(seconds)': metric_value[1]}
                node_disk_io.append(record)
            if metric_name == 'node_memory_MemAvailable_bytes':
                record = {'node': hostname, 'available_memory(bytes)': metric_value[1]}
                node_ram_available_bytes_list.append(record)
            if metric_name == 'accordion_avg_node_network_receive_bytes_total':
                hostname = metric.get('node')
                record = {'node': hostname, 'receive_bandwidth(avg_bytes)': metric_value[1]}
                node_network_receive_bytes_list.append(record)
            if metric_name == 'accordion_avg_node_network_transmit_bytes_total':
                hostname = metric.get('node')
                record = {'node': hostname, 'transmit_bandwidth(avg_bytes)': metric_value[1]}
                node_network_transmit_bytes_list.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)

        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_ram_available_bytes = sorted(node_ram_available_bytes_list, key=lambda k: k['node'])
        orderlist_cpu = sorted(node_cpu_list, key=lambda k: k['node'])
        orderlist_ram = sorted(node_ram_list, key=lambda k: k['node'])
        orderlist_disk_read_latency = sorted(node_disk_read_latency, key=lambda k: k['node'])
        orderlist_disk_write_latency = sorted(node_disk_write_latency, key=lambda k: k['node'])
        orderlist_filesystem_usage = sorted(node_filesystem_usage, key=lambda k: k['node'])
        orderlist_filesystem_size = sorted(node_filesystem_size, key=lambda k: k['node'])
        orderlist_filesystem_free = sorted(node_filesystem_free, key=lambda k: k['node'])
        orderlist_filesystem_avail = sorted(node_filesystem_avail, key=lambda k: k['node'])
        filesystem_usable = usable_space_calculation(orderlist_filesystem_size, orderlist_filesystem_free,
                                                     orderlist_filesystem_avail,
                                                     threshold)
        orderlist_disk_io = sorted(node_disk_io, key=lambda k: k['node'])
        orderlist_network_receive = sorted(node_network_receive_bytes_list, key=lambda k: k['node'])
        orderlist_network_transmit = sorted(node_network_transmit_bytes_list, key=lambda k: k['node'])
        uuid_addition(orderlist_ram, orderlist_uuid)
        uuid_addition(orderlist_cpu, orderlist_uuid)
        uuid_addition(orderlist_disk_read_latency, orderlist_uuid)
        uuid_addition(orderlist_disk_write_latency, orderlist_uuid)
        uuid_addition(orderlist_disk_io, orderlist_uuid)
        uuid_addition(orderlist_filesystem_free, orderlist_uuid)
        uuid_addition(orderlist_filesystem_size, orderlist_uuid)
        uuid_addition(orderlist_filesystem_usage, orderlist_uuid)
        uuid_addition(orderlist_network_transmit, orderlist_uuid)
        uuid_addition(orderlist_network_receive, orderlist_uuid)
        uuid_addition(filesystem_usable, orderlist_uuid)
        for record in orderlist_ram:
            for record1 in orderlist_ram_available_bytes:
                if record1.get('node') == record.get('node'):
                    record['available_memory(bytes)'] = record1.get('available_memory(bytes)')

        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Cpu Usage Results": orderlist_cpu,
                       "Memory Usage Results": orderlist_ram,
                       "Disk Read Latency Results": orderlist_disk_read_latency,
                       "Disk Write Latency Results": orderlist_disk_write_latency,
                       "Filesystem Usage Results": orderlist_filesystem_usage,
                       "Disk Size Results": orderlist_filesystem_size,
                       "Disk Free Space Results": filesystem_usable,
                       "Disk IO Usage Results": orderlist_disk_io,
                       "Node Transmit Bandwidth Results": orderlist_network_transmit,
                       "Node Receive Bandwidth Results": orderlist_network_receive}
    else:
        joined_list = {"timestamp": timestamp(), "minicloud_id": minicloud_id, "Results": {}}

    log = {"metrics_set": "Node Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    rid = requests.post(RID_ip_metrics, json=joined_list)
    if rid.status_code == 200:
        rid_response = "node metrics successfully sent in RID"
    else:
        rid_response = "couldn't reach RID, status error code: " + str(rid.status_code)
    logging.info(rid_response)


def disk_metrics():
    threshold = getDiskPressureThreshold.get_disk_pressure_threshold()
    log = {"disk_pressure_threshold": threshold, "time": str(timestamp())}
    logging.info(json.dumps(log, indent=1))
    query = '{__name__=~"accordion_node_disk_read_latency:1m|accordion_node_disk_write_latency:1m|accordion_node_filesystem_percentage_usage:1m|accordion_node_filesystem_size:1m|accordion_node_filesystem_free:1m|accordion_node_filesystem_avail:1m|accordion_node_disk_io_rate:1m|char_node_location"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    node_disk_read_latency = []
    node_disk_write_latency = []
    node_filesystem_usage = []
    node_filesystem_size = []
    node_filesystem_free = []
    node_disk_io = []
    node_filesystem_avail = []
    node_uuid_list = []
    logging.info('Disk metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']

        for result in results:
            metric_value = result.get('value')
            value = "% .2f" % float(metric_value[1])
            report_time = metric_value[0]
            metric = result.get('metric')
            metric_name = metric.get('__name__')
            hostname = metric.get('instance')
            if metric_name == 'accordion_node_disk_read_latency:1m' and 'nan' not in value:
                partition = metric.get('device')
                record = {'node': hostname, 'device': partition, 'disk_read_latency(percentage)': value}
                node_disk_read_latency.append(record)
            if metric_name == 'accordion_node_disk_write_latency:1m' and 'nan' not in value:
                partition = metric.get('device')
                record = {'node': hostname, 'device': partition, 'disk_write_latency(percentage)': value}
                node_disk_write_latency.append(record)
            if metric_name == 'accordion_node_filesystem_percentage_usage:1m':
                record = {'node': hostname, 'filesystem_usage(percentage)': value}
                node_filesystem_usage.append(record)
            if metric_name == 'accordion_node_filesystem_size:1m':
                record = {'node': hostname, 'disk_total_size(bytes)': metric_value[1]}
                node_filesystem_size.append(record)
            if metric_name == 'accordion_node_filesystem_free:1m':
                record = {'node': hostname, 'disk_free_space(bytes)': metric_value[1]}
                node_filesystem_free.append(record)
            if metric_name == 'accordion_node_filesystem_avail:1m':
                record = {'node': hostname, 'disk_avail_space(bytes)': metric_value[1]}
                node_filesystem_avail.append(record)
            if metric_name == 'accordion_node_disk_io_rate:1m':
                record = {'node': hostname, 'disk_io_time_spent(seconds)': metric_value[1]}
                node_disk_io.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_disk_read_latency = sorted(node_disk_read_latency, key=lambda k: k['node'])
        orderlist_disk_write_latency = sorted(node_disk_write_latency, key=lambda k: k['node'])
        orderlist_filesystem_usage = sorted(node_filesystem_usage, key=lambda k: k['node'])
        orderlist_filesystem_size = sorted(node_filesystem_size, key=lambda k: k['node'])
        orderlist_filesystem_free = sorted(node_filesystem_free, key=lambda k: k['node'])
        orderlist_filesystem_avail = sorted(node_filesystem_avail, key=lambda k: k['node'])
        filesystem_usable = usable_space_calculation(orderlist_filesystem_size, orderlist_filesystem_free,
                                                     orderlist_filesystem_avail,
                                                     threshold)
        orderlist_disk_io = sorted(node_disk_io, key=lambda k: k['node'])
        uuid_addition(orderlist_disk_read_latency, orderlist_uuid)
        uuid_addition(orderlist_disk_write_latency, orderlist_uuid)
        uuid_addition(orderlist_filesystem_usage, orderlist_uuid)
        uuid_addition(orderlist_filesystem_size, orderlist_uuid)
        uuid_addition(orderlist_filesystem_free, orderlist_uuid)
        uuid_addition(orderlist_disk_io, orderlist_uuid)
        uuid_addition(filesystem_usable, orderlist_uuid)
        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {
                           "Disk Read Latency Results": orderlist_disk_read_latency,
                           "Disk Write Latency Results": orderlist_disk_write_latency,
                           "Filesystem Usage Results": orderlist_filesystem_usage,
                           "Disk Size Results": orderlist_filesystem_size,
                           "Disk Free Space Results": filesystem_usable,
                           "Disk IO Usage Results": orderlist_disk_io}}
    else:
        joined_list = {"timestamp": timestamp(), "minicloud_id": minicloud_id, "Results": {}}

    log = {"metrics_set": "Disk Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    aces = requests.post('http://www.psomakelis.eu:1880/acesData', json=joined_list)
    if aces.status_code == 200:
        aces_response = "node metrics successfully sent in ACES"
    else:
        aces_response = "couldn't reach ACES, status error code: " + str(aces.status_code)
    logging.info(aces_response)
    response_status.close()


def namespace_metrics():
    query = '{__name__=~"accordion_max_namespace_cpu_values:1m|accordion_max_namespace_memory_values:1m|accordion_max_namespace_thread_values:1m"}'

    namespace_cpu_list = []
    namespace_memory_list = []
    namespace_thread_list = []
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query,
                                   })
    logging.info('Namespace metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            value = doc.get('value')
            metric = doc.get('metric')
            namespace = metric.get('namespace')
            real_value = value[1]
            report_time = value[0]
            metric_name = metric.get('__name__')
            if metric_name == 'accordion_max_namespace_cpu_values:1m':
                record = {'namespace': namespace, 'max_cpu_usage(seconds)': real_value}
                namespace_cpu_list.append(record)
            if metric_name == 'accordion_max_namespace_memory_values:1m':
                record = {'namespace': namespace, 'max_memory_usage(bytes)': real_value}
                namespace_memory_list.append(record)
            if metric_name == 'accordion_max_namespace_thread_values:1m':
                record = {'namespace': namespace, 'max_namespace_threads': real_value}
                namespace_thread_list.append(record)
        orderlist_cpu = sorted(namespace_cpu_list, key=lambda k: k['namespace'])
        orderlist_memory = sorted(namespace_memory_list, key=lambda k: k['namespace'])
        orderlist_thread = sorted(namespace_thread_list, key=lambda k: k['namespace'])
        joined_list = {'timestamp': report_time, "minicloud_id": minicloud_id,
                       'Results': {'Namespace CPU Results': orderlist_cpu,
                                   'Namespace Memory Results': orderlist_memory,
                                   'Namespace Threads': orderlist_thread}}
    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, 'Results': {}}

    log = {"metrics_set": "Namespace Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))

    producer = Producer()
    try:
        producer.send('accordion.monitoring.currentNamespace', joined_list)
    except:
        logging.info('could not reach Kafka broker')
    response_status.close()


def characterization(type):
    battery_list = []
    ram_list = []
    cpu_list = []
    location_list = []
    disk_list = []
    os_list = []
    gpu_list = []
    gpu_memory_list = []
    query = '{__name__=~"char_node_battery|char_node_cpu_total_cores|char_node_disk_total_size|char_node_location|char_node_os|char_node_ram_total_bytes|char_node_gpu"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('Characterization')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            value = doc.get('value')
            report_time = value[0]
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            if metric_name == 'char_node_battery':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_battery_plugged = metric.get('char_node_plugged_battery')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_battery_plugged': node_battery_plugged, 'node_battery_percent': metric_value}
                battery_list.append(record)
            if metric_name == 'char_node_ram_total_bytes':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_ram_total_bytes': metric_value}
                ram_list.append(record)
            if metric_name == 'char_node_cpu_total_cores':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                arch = metric.get('char_node_arch')
                bits = metric.get('char_node_bits')
                brand = metric.get('char_node_brand')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_cpu_arch': arch, 'node_cpu_bits': bits, 'node_cpu_brand': brand,
                          'node_cpu_cores': metric_value}
                cpu_list.append(record)
            if metric_name == 'char_node_location':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                city = metric.get('char_node_city')
                continent = metric.get('char_node_continent')
                country = metric.get('char_node_country')
                latitude = metric.get('char_node_latitude')
                longitude = metric.get('char_node_longitude')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_city': city, 'node_continent': continent, 'node_country': country,
                          'node_latitude': latitude, 'node_longitude': longitude}
                location_list.append(record)
            if metric_name == 'char_node_disk_total_size':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_disk_total_size': metric_value}
                disk_list.append(record)
            if metric_name == 'char_node_os':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                os_name = metric.get('char_node_os_name')
                os_version = metric.get('char_node_os_version')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_os_name': os_name, 'node_os_version': os_version}
                os_list.append(record)
            if metric_name == 'char_node_gpu':
                metric_value = value[1]
                node_class = metric.get('char_node_class')
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                gpu_id = metric.get('char_node_gpu_id')
                instance = metric.get('instance')
                ip = instance.replace(':5001', '')
                gpu_model = metric.get('char_node_gpu_model')
                gpu_type = metric.get('char_node_gpu_type')
                record = {'node_type': node_class, 'node_name': node_name, 'node_uuid': node_uuid, 'node_ip': ip,
                          'node_gpu_model': gpu_model, 'node_gpu_type': gpu_type, 'node_gpu_id': gpu_id,
                          'quantity': metric_value}
                gpu_list.append(record)

        orderlist_cpu = sorted(cpu_list, key=lambda k: k['node_name'])
        orderlist_ram = sorted(ram_list, key=lambda k: k['node_name'])
        orderlist_disk = sorted(disk_list, key=lambda k: k['node_name'])
        orderlist_battery = sorted(battery_list, key=lambda k: k['node_name'])
        orderlist_location = sorted(location_list, key=lambda k: k['node_name'])
        orderlist_os = sorted(os_list, key=lambda k: k['node_name'])
        orderlist_gpu = sorted(gpu_list, key=lambda k: k['node_gpu_id'])

        joined_list = {
            "timestamp": report_time, "minicloud_id": minicloud_id, 'CPU Characterization': orderlist_cpu,
            'Memory Characterization': orderlist_ram,
            'Disk Characterization': orderlist_disk,
            'Battery Characterization': orderlist_battery,
            'Location Characterization': orderlist_location, 'OS Characterization': orderlist_os,
            'GPU Characterization': orderlist_gpu}

        log = {"metrics_set": "Characterization", "time": str(timestamp()), "json": joined_list}
        logging.info(json.dumps(log, indent=1))
        if type == 'rid':
            r = requests.post(RID_ip_characterization, json=joined_list)
            if r.status_code == 200:
                response = "characterization data successfully sent in RID"
            else:
                response = "couldn't reach RID, status error code: " + str(r.status_code)
        if type == 'echoserver':
            r = requests.post(echoserver_ip_gpu, json=log)
            if r.status_code == 200:
                response = "characterization data successfully sent in echoserver"
            else:
                response = "couldn't reach echoserver, status error code: " + str(r.status_code)

        logging.info(response)
        response_status.close()


def Grafana_metrics_set():
    query = '{__name__=~"accordion_pod_cpu_usage_seconds_total|accordion_pod_memory_usage_bytes|accordion_pod_threads|accordion_pod_network_receive_bytes_total|accordion_pod_network_transmit_bytes_total|char_node_location"}'

    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('Grafana Pod Metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    joined_list = []
    cpu_list = []
    ram_list = []
    thread_list = []
    receive_list = []
    transmit_list = []
    node_uuid_list = []
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            value = doc.get('value')
            metric_value = value[1]
            report_time = value[0]
            pod = metric.get('pod')
            node = metric.get('node')
            metric_name = metric.get("__name__")
            if metric_name == "accordion_pod_cpu_usage_seconds_total":
                record = {'node': node, 'pod': pod, "pod_cpu_usage(seconds)": metric_value}
                cpu_list.append(record)
            if metric_name == "accordion_pod_memory_usage_bytes":
                record = {'node': node, 'pod': pod, "pod_memory_usage(bytes)": metric_value}
                ram_list.append(record)
            if metric_name == "accordion_pod_threads":
                record = {'node': node, 'pod': pod, "pod_threads": metric_value}
                thread_list.append(record)
            if metric_name == "accordion_pod_network_receive_bytes_total":
                record = {'node': node, "receive_bandwidth(bytes)": metric_value}
                receive_list.append(record)
            if metric_name == "accordion_pod_network_transmit_bytes_total":
                record = {'node': node, "transmit_bandwidth(bytes)": metric_value}
                transmit_list.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_cpu = sorted(cpu_list, key=lambda k: k['pod'])
        orderlist_ram = sorted(ram_list, key=lambda k: k['pod'])
        orderlist_thread = sorted(thread_list, key=lambda k: k['pod'])
        orderlist_receive = sorted(receive_list, key=lambda k: k['node'])
        orderlist_transmit = sorted(transmit_list, key=lambda k: k['node'])
        uuid_addition(orderlist_cpu, orderlist_uuid)
        uuid_addition(orderlist_ram, orderlist_uuid)
        uuid_addition(orderlist_thread, orderlist_uuid)
        uuid_addition(orderlist_receive, orderlist_uuid)
        uuid_addition(orderlist_transmit, orderlist_uuid)
        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {"Pod CPU Usage Results": orderlist_cpu,
                                   "Pod Memory Usage Results": orderlist_ram,
                                   "Pod Threads Results": orderlist_thread,
                                   "Pod Receive Bandwidth Results": orderlist_receive,
                                   "Pod Transmit Bandwidth Results": orderlist_transmit}}
    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, "Results": {}}

    producer = Producer()
    try:
        producer.send("accordion.monitoring.GrafanaMetrics", joined_list)
    except:
        logging.info('could not reach Kafka broker')

    log = {"metrics_set": "Grafana Pod metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    response_status.close()


def Grafana_VM_metrics_set():
    query = '{__name__=~"accordion_vm_cpu_time_usage|accordion_vm_memory_usage_bytes_values|windows_system_threads|windows_net_bytes_received_total|windows_net_bytes_sent_total|accordion_vm_info|char_node_location"}'

    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('Grafana VM metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    joined_list = []
    cpu_list = []
    ram_list = []
    thread_list = []
    receive_list = []
    transmit_list = []
    info = []
    node_uuid_list = []
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            value = doc.get('value')
            metric_value = value[1]
            report_time = value[0]
            metric_name = metric.get("__name__")
            if metric_name == "accordion_vm_cpu_time_usage":
                instance = metric.get('instance')
                record = {'vm_ip': instance, "vm_cpu_usage(seconds)": metric_value}
                cpu_list.append(record)
            if metric_name == "accordion_vm_memory_usage_bytes_values":
                instance = metric.get('instance')
                record = {'vm_ip': instance, "vm_memory_usage(bytes)": metric_value}
                ram_list.append(record)
            if metric_name == "windows_system_threads":
                instance = metric.get('instance')
                record = {'vm_ip': instance, "vm_threads": metric_value}
                thread_list.append(record)
            if metric_name == "windows_net_bytes_received_total":
                instance = metric.get('instance')
                record = {'vm_ip': instance, "receive_bandwidth(bytes)": metric_value}
                receive_list.append(record)
            if metric_name == "windows_net_bytes_sent_total":
                instance = metric.get('instance')
                record = {'vm_ip': instance, "transmit_bandwidth(bytes)": metric_value}
                transmit_list.append(record)
            if metric_name == "accordion_vm_info":
                namespace = metric.get('namespace')
                node = metric.get('node')
                host_ip = metric.get('host_ip')
                vm_ip = metric.get('pod_ip')
                vm_name = metric.get('created_by_name')
                record = {'node': node, 'node_ip': host_ip, 'namespace': namespace, 'vm_name': vm_name, 'vm_ip': vm_ip}
                info.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_info = sorted(info, key=lambda k: k['node'])
        uuid_addition(orderlist_info, orderlist_uuid)

        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {"VM CPU Usage Results": cpu_list,
                                   "VM Memory Usage Results": ram_list,
                                   "VM Threads Results": thread_list,
                                   "VM Receive Bandwidth Results": receive_list,
                                   "VM Tramsmit Bandwidth Results": transmit_list,
                                   "VM Info Results": info}}
    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, "Results": {}}

    log = {"metrics_set": "Grafana VM metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    producer = Producer()
    try:
        producer.send("accordion.monitoring.GrafanaMetrics", joined_list)
    except:
        logging.info('could not reach Kafka broker')
    response_status.close()


def vm_metrics():
    query = '{__name__=~"accordion_max_vm_cpu_rate_usage_values:1m|accordion_max_vm_memory_usage_bytes_values:1m|accordion_max_vm_system_threads_values:1m|accordion_max_vm_transmit_bytes_values:1m|accordion_max_vm_receive_bytes:1m|accordion_vm_info|char_node_location"}or kube_pod_labels{pod=~"virt-launcher.*"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('VM metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    vm_cpu_list = []
    vm_memory_list = []
    vm_thread_list = []
    vm_receive_bytes_list = []
    vm_transmit_bytes_list = []
    vm_info = []
    labels_list = []
    node_uuid_list = []
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            value = doc.get('value')
            metric_value = value[1]
            report_time = value[0]
            ip = metric.get('instance')
            if metric_name == "accordion_max_vm_cpu_rate_usage_values:1m":
                record = {'vm_ip': ip, 'vm_cpu_usage(seconds)': metric_value}
                vm_cpu_list.append(record)
            if metric_name == "accordion_max_vm_memory_usage_bytes_values:1m":
                record = {'vm_ip': ip, 'vm_memory_usage(bytes)': metric_value}
                vm_memory_list.append(record)
            if metric_name == "accordion_max_vm_system_threads_values:1m":
                record = {'vm_ip': ip, 'vm_threads': metric_value}
                vm_thread_list.append(record)
            if metric_name == "accordion_max_vm_transmit_bytes_values:1m":
                record = {'vm_ip': ip, 'receive_bandwidth(bytes)': metric_value}
                vm_receive_bytes_list.append(record)
            if metric_name == "accordion_max_vm_receive_bytes:1m":
                record = {'vm_ip': ip, 'transmit_bandwidth(bytes)': metric_value}
                vm_transmit_bytes_list.append(record)
            if metric_name == "kube_pod_labels":
                launcher = metric.get('pod')
                label_component = metric.get('label_component')
                record = {'launcher': launcher, 'label_component': label_component}
                labels_list.append(record)
            if metric_name == "accordion_vm_info":
                launcher = metric.get('pod')
                ip = metric.get('pod_ip')
                host_ip = metric.get('host_ip')
                node = metric.get('node')
                namespace = metric.get('namespace')
                kind = metric.get('created_by_kind')
                vm = metric.get('created_by_name')
                record = {'vm': vm, 'vm_ip': ip, 'launcher': launcher, 'namespace': namespace, 'created_by_kind': kind,
                          'node': node,
                          'node_ip': host_ip}
                vm_info.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_vm_info = sorted(vm_info, key=lambda k: k['node'])
        uuid_addition(orderlist_vm_info, orderlist_uuid)
        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {"VM CPU Usage Results": vm_cpu_list,
                                   "VM Memory Usage Results": vm_memory_list,
                                   "VM Threads Results": vm_thread_list,
                                   "VM Receive Bandwidth Results": vm_receive_bytes_list,
                                   "VM Tramsmit Bandwidth Results": vm_transmit_bytes_list,
                                   "VM Info Results": vm_info,
                                   "VM Labels Results": labels_list}}

    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, 'Results': {}}

    log = {"metrics_set": "VM Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))

    producer = Producer()
    try:
        producer.send('accordion.monitoring.currentVM', joined_list)
    except:
        logging.info('could not reach Kafka broker')
    response_status.close()


def pod_information():
    external_ips = []
    pod_status_list = []
    pod_info_list = []
    load_balancer_list = []
    label_list = []
    service = ""
    query = 'kube_pod_status_phase{pod=~"acc-.*"} ==1 or kube_pod_info{pod=~"acc-.*"}or kube_service_status_load_balancer_ingress{namespace=~"acc-.*"} or kube_pod_labels{pod=~"acc-.*"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    response_status.status_code
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            value = doc.get('value')
            report_time = value[0]
            phase = metric.get('phase')
            namespace = metric.get('namespace')
            pod = metric.get('pod')
            if metric_name == 'kube_pod_status_phase':
                record = {"pod_status": phase, 'pod': pod, 'namespace': namespace,
                          'started': report_time,
                          'timezone': 'UTC'}
                pod_status_list.append(record)

            if metric_name == 'kube_pod_info':
                kind = metric.get('created_by_kind')
                host_ip = metric.get('host_ip')
                node = metric.get('node')
                pod_ip = metric.get('pod_ip')
                record = {'pod': pod, 'pod_ip': pod_ip, 'namespace': namespace, 'created_by_kind': kind,
                          'node': node,
                          'node_ip': host_ip}
                pod_info_list.append(record)
            if metric_name == 'kube_pod_labels':
                label_component = metric.get('label_component')
                record = {'pod': pod, 'label_component': label_component}
                label_list.append(record)
            if metric_name == 'kube_service_status_load_balancer_ingress':
                service = metric.get('service')
                if service:
                    ip = metric.get('ip')
                    external_ips.append(ip)

        load_balancer_list.append({'service': service, 'external_ip': external_ips})
        orderlist_status_list = sorted(pod_status_list, key=lambda k: k['pod'])
        orderlist_info_list = sorted(pod_info_list, key=lambda k: k['pod'])
        orderlist_label_list = sorted(label_list, key=lambda k: k['pod'])
        if orderlist_label_list and orderlist_info_list and orderlist_status_list and load_balancer_list:
            joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                           "Results": {"Pod_Status_Phase_Results": orderlist_status_list,
                                       "Pod_Info_Results": orderlist_info_list,
                                       "Load_Balancer_Results": load_balancer_list,
                                       "Label_Results": orderlist_label_list}}
            log = {"time": str(timestamp()), "json": joined_list}
            logging.info(json.dumps(log, indent=1))

            producer = Producer()
            producer.send('accordion.monitoring.podInformation', joined_list)


def vminformation():
    vm_status_list = []
    external_ips = []
    label_list = []
    load_balancer_list = []
    label_vm_list = []
    pod_info_list = []
    # Slice string to remove last 2 characters from string

    query = 'kubevirt_virtual_machine_status{vm_name=~"acc-.*"} or kube_service_status_load_balancer_ingress{service=~"acc-.*",namespace=~"acc-.*"} or kubevirt_virtual_machine_labels{vm_name=~"acc-.*",vm_namespace=~"acc-.*"} or kube_pod_info{namespace=~"acc-.*",pod=~"virt.*"}'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    response_status.status_code
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            if metric_name == 'kubevirt_virtual_machine_status':
                value = doc.get('value')
                report_time = value[0]
                vm_name = metric.get('vm_name')
                vm_namespace = metric.get('vm_namespace')
                vm_ip = metric.get('vm_ip_address')
                vm_phase = metric.get('vm_phase')
                startedAt = metric.get('startedAt')
                node_name = metric.get('node_name')
                record = {"vm_status": vm_phase, 'vm': vm_name, 'namespace': vm_namespace, 'vm_ip': vm_ip,
                          'node': node_name,
                          'started': startedAt,
                          'timezone': 'UTC'}
                vm_status_list.append(record)
            if metric_name == 'kube_service_status_load_balancer_ingress':
                service = metric.get('service')
                namespace = metric.get('namespace')
                for record in vm_status_list:
                    if namespace == record.get('namespace') and service:
                        ip = metric.get('ip')
                        external_ips.append(ip)
                        load_balancer_list.append({'service': service, 'external_ip': external_ips})
            if metric_name == 'kubevirt_virtual_machine_labels':
                label_component = metric.get('component')
                label_vm_list.append(label_component)
                record = {'vm': vm_name, 'label_component': label_component}
                label_list.append(record)
            if metric_name == 'kube_pod_info':
                kind = metric.get('created_by_kind')
                host_ip = metric.get('host_ip')
                pod = metric.get('pod')
                namespace = metric.get('namespace')
                node = metric.get('node')
                pod_ip = metric.get('pod_ip')
                record = {'pod': pod, 'pod_ip': pod_ip, 'vm_namespace': namespace, 'created_by_kind': kind,
                          'node': node,
                          'node_ip': host_ip}
                pod_info_list.append(record)
        orderlist = sorted(vm_status_list, key=lambda k: k['vm'])
        orderlist_label_list = sorted(label_list, key=lambda k: k['vm'])
        orderlist_info_list = sorted(pod_info_list, key=lambda k: k['pod'])
        if orderlist and orderlist_info_list and orderlist_label_list and load_balancer_list:
            joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                           "Results": {"VM_Status_Phase_Results": orderlist, "Pod_Info_Results": orderlist_info_list,
                                       "Load_Balancer_Results": load_balancer_list,
                                       "Label_Results": orderlist_label_list}}
            log = {"time": str(timestamp()), "json": joined_list}
            logging.info(json.dumps(log, indent=1))

            producer = Producer()
            producer.send('accordion.monitoring.vmInformation', joined_list)


def platform_metrics():
    # echoserver metrics
    cpu_echoserver_query = 'accordion_echoserver_cpu_usage_seconds_total'
    ram_echoserver_query = 'accordion_echoserver_memory_usage_bytes'
    threads_echoserver_query = 'accordion_echoserver_threads'
    # nlm metrics
    cpu_nlm_query = 'accordion_nlm_cpu_usage_seconds_total'
    ram_nlm_query = 'accordion_nlm_memory_usage_bytes'
    threads_nlm_query = 'accordion_nlm_threads'
    # aces metrics
    cpu_aces_query = 'accordion_aces_cpu_usage_seconds_total'
    ram_aces_query = 'accordion_aces_memory_usage_bytes'
    threads_aces_query = 'accordion_aces_threads'
    # aces sync
    cpu_aces_sync_query = 'accordion_aces_cpu_sync_usage_seconds_total'
    ram_aces_sync_query = 'accordion_aces_sync_memory_usage_bytes'
    threads_aces_sync_query = 'accordion_aces_sync_threads'
    # cdi metrics
    cpu_cdi_query = 'accordion_cdi_cpu_usage_seconds_total'
    ram_cdi_query = 'accordion_cdi_memory_usage_bytes'
    threads_cdi_query = 'accordion_cdi_threads'
    # dlf metrics
    cpu_dlf_query = 'accordion_dlf_cpu_usage_seconds_total'
    ram_dlf_query = 'accordion_dlf_memory_usage_bytes'
    threads_dlf_query = 'accordion_dlf_threads'
    # kube-system metrics
    cpu_kube_system_query = 'accordion_kube_system_cpu_usage_seconds_total'
    ram_kube_system_query = 'accordion_kube_system_memory_usage_bytes'
    threads_kube_system_query = 'accordion_kube_system_threads'
    # kubevirt metrics
    cpu_kubevirt_query = 'accordion_kubevirt_cpu_usage_seconds_total'
    ram_kubevirt_query = 'accordion_kubevirt_memory_usage_bytes'
    threads_kubevirt_query = 'accordion_kubevirt_threads'
    # monitoring metrics
    cpu_monitoring_query = 'accordion_monitoring_cpu_usage_seconds_total'
    ram_monitoring_query = 'accordion_monitoring_memory_usage_bytes'
    threads_monitoring_query = 'accordion_monitoring_threads'
    # rid metrics
    cpu_rid_query = 'accordion_rid_cpu_usage_seconds_total'
    ram_rid_query = 'accordion_rid_memory_usage_bytes'
    threads_rid_query = 'accordion_rid_threads'
    query = cpu_echoserver_query + ' or ' + cpu_nlm_query + ' or ' + cpu_aces_query + ' or ' + cpu_aces_sync_query + \
            ' or ' + cpu_cdi_query + ' or ' + cpu_dlf_query + ' or ' + cpu_kube_system_query + ' or ' + cpu_kubevirt_query + ' or ' + cpu_monitoring_query + \
            ' or ' + cpu_rid_query + ' or ' + ram_echoserver_query + ' or ' + ram_nlm_query + ' or ' + ram_aces_query + ' or ' + ram_aces_sync_query + \
            ' or ' + ram_cdi_query + ' or ' + ram_dlf_query + ' or ' + ram_kube_system_query + ' or ' + ram_kubevirt_query + ' or ' + ram_monitoring_query + \
            ' or ' + ram_rid_query + ' or ' + threads_echoserver_query + ' or ' + threads_nlm_query + ' or ' + threads_aces_query + ' or ' + threads_aces_sync_query + \
            ' or ' + threads_cdi_query + ' or ' + threads_dlf_query + ' or ' + threads_kube_system_query + ' or ' + threads_kubevirt_query + ' or ' + threads_monitoring_query + \
            ' or ' + threads_rid_query + ' or char_node_location'
    response_status = requests.get(prometheus_query,
                                   params={
                                       'query': query
                                   })
    logging.info('Platform metrics')
    logging.info('Prometheus status code: ' + str(response_status.status_code))
    pod_cpu_list = []
    pod_memory_list = []
    pod_thread_list = []
    node_uuid_list = []
    if response_status.status_code == 200 and response_status.json()['data']['result']:
        results = response_status.json()['data']['result']
        for doc in results:
            metric = doc.get('metric')
            metric_name = metric.get('__name__')
            value = doc.get('value')
            metric_value = value[1]
            report_time = value[0]
            pod = metric.get('pod')
            node = metric.get('node')
            namespace = metric.get('namespace')
            if metric_name == cpu_rid_query or metric_name == cpu_monitoring_query \
                    or metric_name == cpu_kubevirt_query or metric_name == cpu_aces_query or metric_name == cpu_kube_system_query or metric_name == cpu_aces_sync_query \
                    or metric_name == cpu_nlm_query or metric_name == cpu_echoserver_query or metric_name == cpu_cdi_query or metric_name == cpu_dlf_query:
                record = {'namespace': namespace, 'node': node, 'pod': pod,
                          'component_cpu_usage(seconds)': metric_value}
                pod_cpu_list.append(record)
            if metric_name == ram_rid_query or metric_name == ram_monitoring_query \
                    or metric_name == ram_kubevirt_query or metric_name == ram_aces_query or metric_name == ram_kube_system_query or metric_name == ram_aces_sync_query \
                    or metric_name == ram_nlm_query or metric_name == ram_echoserver_query or metric_name == ram_cdi_query or metric_name == ram_dlf_query:
                record = {'namespace': namespace, 'node': node, 'pod': pod,
                          'component_memory_usage(bytes)': metric_value}
                pod_memory_list.append(record)
            if metric_name == threads_rid_query or metric_name == threads_monitoring_query \
                    or metric_name == threads_kubevirt_query or metric_name == threads_aces_query or metric_name == threads_kube_system_query or metric_name == threads_aces_sync_query \
                    or metric_name == threads_nlm_query or metric_name == threads_echoserver_query or metric_name == threads_cdi_query or metric_name == threads_dlf_query:
                record = {'namespace': namespace, 'node': node, 'pod': pod, 'component_threads': metric_value}
                pod_thread_list.append(record)
            if metric_name == 'char_node_location':
                node_name = metric.get('char_node_name')
                node_uuid = metric.get('char_node_uuid')
                record = {'node': node_name, 'uuid': node_uuid}
                node_uuid_list.append(record)
        orderlist_uuid = sorted(node_uuid_list, key=lambda k: k['node'])
        orderlist_cpu = sorted(pod_cpu_list, key=lambda k: k['pod'])
        orderlist_ram = sorted(pod_memory_list, key=lambda k: k['pod'])
        orderlist_thread = sorted(pod_thread_list, key=lambda k: k['pod'])
        uuid_addition(orderlist_ram, orderlist_uuid)
        uuid_addition(orderlist_cpu, orderlist_uuid)
        uuid_addition(orderlist_thread, orderlist_uuid)
        joined_list = {"timestamp": report_time, "minicloud_id": minicloud_id,
                       "Results": {"Pod CPU Usage Results": orderlist_cpu,
                                   "Pod Memory Usage Results": orderlist_ram,
                                   "Pod Threads Results": orderlist_thread}}

    else:
        joined_list = {'timestamp': timestamp(), "minicloud_id": minicloud_id, 'Results': {}}

    log = {"metrics_set": "Platform Metrics", "time": str(timestamp()), "json": joined_list}
    logging.info(json.dumps(log, indent=1))
    producer = Producer()
    try:
        producer.send('accordion.monitoring.platform', joined_list)
    except:
        logging.info('could not reach Kafka broker')
    response_status.close()
