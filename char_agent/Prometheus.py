import time
import subprocess
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.metrics_core import GaugeMetricFamily
import characterization
import os
import logging

logging.basicConfig(level=logging.INFO)


def convert_bytes(bytes):
    output = 0
    if 'M' in bytes:
        number = bytes.replace('M', ' ')
        output = int(number) * 1024 * 1024
    if 'G' in bytes:
        number = bytes.replace('G', ' ')
        output = int(number) * 1024 * 1024 * 1024
    return output


class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        # Get nodes information and get local node services list from response
        currentpath = os.getcwd()
        char_node_name = os.getenv("NODE_NAME", "node_name")
        plugged, char_node_battery = characterization.get_battery()
        char_node_class = characterization.get_host_type()
        GPU_names = []
        characterization.generate_uuid()
        home_uuid = currentpath + "/uuid.txt"
        with open(home_uuid) as file:
            char_node_uuid = file.readline()
        char_node_location = characterization.get_location()
        region = char_node_location.get('region')
        location = region.get('location')
        country = region.get('country')
        continent = region.get('continent')
        latitude = region.get('latitude')
        longitude = region.get('longitude')
        char_node_disk = characterization.get_disk()
        char_node_cpu = characterization.get_cpu()
        cpu = char_node_cpu.get('CPU')
        brand = cpu.get('model')
        CPUarch = cpu.get('Arch')
        CPUenergy = cpu.get('energy_watt')
        CPUbits = cpu.get('bits')
        CPUcores = cpu.get('cores')
        char_node_ram = characterization.get_ram()
        char_node_os = characterization.get_os()
        char_os = char_node_os.get('OS')
        os_name = char_os.get('OS_name')
        os_version = char_os.get('OS_version')
        if 'arm' in CPUarch:
            char_node_class = 'RPi'
        if 'with' in brand or 'arm' in CPUarch:
            dedicatedGPU = 'Integrated graphics processing'
        else:
            dedicatedGPU = 'Dedicated graphics processing'
        # metric1
        if plugged:
            label_plugged = 'true'
        if not plugged:
            label_plugged = 'false'
        battery_metric = GaugeMetricFamily('char_node_battery', 'Battery percentage of the device',
                                           labels=['char_node_name', 'char_node_class', 'char_node_uuid',
                                                   'char_node_plugged_battery'])

        battery_metric.add_metric(
            [char_node_name, char_node_class, char_node_uuid, label_plugged],
            char_node_battery)
        yield battery_metric
        # metric2
        ram_metric = GaugeMetricFamily('char_node_ram_total_bytes', 'Total RAM of the device',
                                       labels=['char_node_name', 'char_node_class', 'char_node_uuid'])
        ram_metric.add_metric(
            [char_node_name, char_node_class, char_node_uuid],
            char_node_ram)
        yield ram_metric
        # metric3
        cpu_metric = GaugeMetricFamily('char_node_cpu_total_cores', 'Number of CPU cores of a device.',
                                       labels=['char_node_name', 'char_node_class', 'char_node_uuid', 'char_node_brand',
                                               'char_node_arch', 'char_node_bits'])
        cpu_metric.add_metric(
            [char_node_name, char_node_class, char_node_uuid, brand, CPUarch, CPUbits],
            CPUcores)
        yield cpu_metric
        cpu_energy_metric = GaugeMetricFamily('char_node_cpu_energy_watt', 'Energy consumption of CPU in Watt.',
                                       labels=['char_node_name', 'char_node_class', 'char_node_uuid', 'char_node_brand',
                                               'char_node_arch', 'char_node_bits'])
        cpu_energy_metric.add_metric(
            [char_node_name, char_node_class, char_node_uuid, brand, CPUarch, CPUbits],
            CPUenergy)
        yield cpu_energy_metric
        # metric4
        location_metric = GaugeMetricFamily('char_node_location', 'Location of a device.',
                                            labels=['char_node_name', 'char_node_class', 'char_node_uuid',
                                                    'char_node_city',
                                                    'char_node_country', 'char_node_continent', 'char_node_latitude',
                                                    'char_node_longitude'])
        if location or country or continent or latitude or longitude:
            location_metric.add_metric([char_node_name, char_node_class, char_node_uuid, location, country, continent,
                                        str(latitude), str(longitude)], 1)
        else:
            location_metric.add_metric([char_node_name, char_node_class, char_node_uuid, location, country, continent,
                                        str(latitude), str(longitude)], 0)
        yield location_metric

        # metric5
        disk_metric = GaugeMetricFamily('char_node_disk_total_size', 'size of a disk of a device.',
                                        labels=['char_node_name', 'char_node_class', 'char_node_uuid'])
        disk_metric.add_metric([char_node_name, char_node_class, char_node_uuid], char_node_disk)
        yield disk_metric
        # metric6
        os_metric = GaugeMetricFamily('char_node_os', 'Information about the os of a device.',
                                      labels=['char_node_name', 'char_node_class', 'char_node_uuid',
                                              'char_node_os_name', 'char_node_os_version'])
        if os_name or os_version:
            os_metric.add_metric([char_node_name, char_node_class, char_node_uuid, os_name, os_version], 1)
        else:
            os_metric.add_metric([char_node_name, char_node_class, char_node_uuid, os_name, os_version], 0)
        yield os_metric

        GPU = characterization.get_gpu_model(CPUarch)
        # metric7
        gpu_metric = GaugeMetricFamily('char_node_gpu', 'Information about the gpu of a device.',
                                       labels=['char_node_name', 'char_node_class', 'char_node_uuid',
                                               'char_node_gpu_model', 'char_node_gpu_type', "char_node_gpu_id"])


        gpu_list = GPU.get("GPU_list")
        if gpu_list:
            for gpu in gpu_list:
                GPUname = gpu.get("GPU_name")
                id = gpu.get("id")
                quantity = gpu.get("quantity")

                gpu_metric.add_metric(
                    ([char_node_name, char_node_class, char_node_uuid, GPUname, dedicatedGPU, str(id)]), quantity)

        else:
            GPUname = "not available GPU"
            dedicatedGPU = "not available GPU"
            gpu_metric.add_metric(
                ([char_node_name, char_node_class, char_node_uuid, GPUname, dedicatedGPU, "0"]), 0)

        yield gpu_metric


if __name__ == '__main__':
    start_http_server(5001)
    # Define the path to your shell script
    home = os.getcwd()
    script_path = home+'/run-powerjoular.sh'
    # Run the shell script
    subprocess.run([script_path], shell=True)
    while not os.path.exists(home+'/output.csv'):
        # Wait for a short time before checking again
        time.sleep(1)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(5)
