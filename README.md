# Table of Contents
- [EdgeCloud Mon](#edgecloud-mon)
- [Architecture](#architecture)
- [ACCORDION Case](#accordion-case)
- [Core Queries](#core-queries)
- [Docker Images](#docker-images)

# EdgeCloud Mon

EdgeCloud Mon is a lightweight monitoring tool designed to oversee K3s clusters. It focuses on providing information about hosts (physical or virtual machines) and application components, regardless of their deployment method (K3s pods or Kubevirt virtual machines). This data is crucial for cloud platforms to enhance their orchestration. EdgeCloud Mon uses the Prometheus monitoring system, employing exporters to gather the necessary metrics for monitoring. 

The monitoring stack primarily utilizes Kubernetes definition files from the <a href="https://github.com/carlosedp/cluster-monitoring" target="_blank">Cluster Monitoring stack for ARM / X86-64 platforms</a> project to simplify the installation process on K3s clusters. Certain files have been modified to suit the requirements of the [ACCORDION platform case](#accordion-case), and new files have been added to deploy custom-developed exporters within the monitoring stack. The installation process scripts can be found in the <a href="https://github.com/f-coda/EdgeCloud-Mon/tree/main/monitoring_installation"> monitoring_installation </a> folder.
## Architecture
![alt text](EdgeCloud%20Mon.drawio.png)
* <a href="https://github.com/prometheus/node_exporter" target="_blank">Node exporter </a>exporter for hardware and OS metrics
* <a href="https://github.com/kubernetes-sigs/prometheus-adapter"> Prometheus adapter</a> which is an implementation of the Kubernetes resource metrics, custom metrics, and external metrics APIs
* <a href="https://github.com/kubernetes/kube-state-metrics"> Kube-state-metrics </a> expose critical metrics about the condition of a Kubernetes cluster, it generates them from the Kubernetes API server
* <a href= "https://prometheus.io/"> Prometheus </a>
* <a href="https://github.com/prometheus-operator/prometheus-operator"> Prometheus Operator </a> allows for dynamic configuration of targets on Prometheus
* <a href="https://github.com/f-coda/EdgeCloud-Mon/tree/main/char_agent"> Characterization agent </a> provides detailed information about the node, including city, country, continent, latitude, and longitude. It can differentiate between physical and virtual machines, describe CPU model, architecture, bits, and cores. It also exports RAM and disk size, identifies the operating system along with its version, and detects the presence of a battery or GPU in the device.
* <a href="https://github.com/f-coda/EdgeCloud-Mon/tree/main/kubevirt_exporter">Kubevirt exporter </a> communicates with the Kubevirt API to retrieve the status of virtual machines, specifically whether they are running or not

## ACCORDION Case
![alt text](monitoring%20architecture.png)
EdgeCloud Mon has already been use in ACCORDION platform. The ACCORDION platform was financially supported by the European Union's Horizon 2020 research and innovation programme through grant agreement no 871793. The platform's vision was to simplify the deployment of applications with diverse requirements spanning the Cloud and Edge continuum. To achieve this goal, the platform employed both K3s and Kubevirt for application deployment, thereby supporting deployment units in the form of pods and virtual machines.

Due to the utilization of multiple Edge and Cloud K3s clusters in ACCORDION, a central monitoring hub was imperative. To achieve this, a Kafka broker was configured with specific topics designated to store various monitoring metrics. Within each EdgeCloud monitoring instance, a producer named <a href="https://github.com/f-coda/EdgeCloud-Mon/tree/main/monitoringapi">monitoringapi</a> was utilized. This MonitoringAPI interacted with Prometheus at regular intervals, retrieving the metric sets and transmitting them to the Kafka broker. Subsequently, an ElasticSearchDB accessed these metric sets, enabling a central Grafana system to retrieve and display these metrics on dashboards. 

The image illustrates the utilization of the monitoring stack in the ACCORDION platform. However, this repository doesn't offer the setup for components that reside on Cloud (Kafka Broker, ElasticSearchDB, Grafana).
Instead, it provides the configuration for the Edge environment. This configuration can be used to monitor a K3s cluster installed on either Edge or Cloud resources.

## Core Queries
| Category              | Metric                                    | Description                                                 |
|-----------------------|--------------------------------------------|-------------------------------------------------------------|
| **Windows VM Monitoring** | `accordion_vm_cpu_rate_usage_values`    | Returns the rate CPU usage of a vm                         |
|                        | `accordion_vm_memory_usage_bytes_values` | Returns the total RAM usage of a vm                        |
|                        | `accordion_vm_cpu_time_usage`            | Returns the total CPU usage of a vm                        |
|                        | `accordion_vm_info`                      | Returns vm name and vm IP                                  |
| **Pod Monitoring**      | `accordion_pod_network_transmit_bytes_total` | Returns the total transmit bandwidth of a pod          |
|                        | `accordion_pod_network_receive_bytes_total`  | Returns the total receive bandwidth of a pod           |
|                        | `accordion_pod_cpu_usage_seconds_total`      | Returns the total CPU usage of a pod                   |
|                        | `accordion_pod_memory_usage_bytes`            | Returns the total RAM usage of a pod                   |
|                        | `accordion_pod_threads`                       | Returns the number of threads inside a pod            |
| **Infrastructure Monitoring** | `accordion_node_cpu_rate_usage:1m`       | Returns the CPU usage percentage of the host in the last minute |
|                              | `accordion_node_memory_avg_usage:1m`      | Returns the RAM usage percentage of the host in the last minute |
|                              | `accordion_node_disk_read_latency:1m`     | Returns the disk read latency of the last minute in percentage |
|                              | `accordion_node_disk_write_latency:1m`    | Returns the disk write latency of the last minute in percentage |
|                              | `accordion_node_filesystem_percentage_usage:1m` | Returns the filesystem usage of the laste minute in percentage |
|                              | `accordion_node_filesystem_size:1m`        | Returns the filesystem size of the last minute         |
|                              | `accordion_node_filesystem_avail:1m`       | Returns the available space of the filesystem in the last minute |
|                              | `accordion_node_filesystem_free:1m`        | Returns the free space of the filesystem in the last minute |
|                              | `accordion_node_disk_io_rate:1m`           | Returns the rate of disk io in the last minute          |
| **Characterization**        | `char_node_battery`                        | Battery percentage of the device                         |
|                              | `char_node_ram_total_bytes`                | Total RAM of the device                                  |
|                              | `char_node_cpu_total_cores`                | Number of CPU cores of a device                         |
|                              | `char_node_location'`                      | Location of a device                                     |
|                              | `char_node_disk_total_size`                | Size of a disk of a device                               |
|                              | `char_node_os`                             | Information about the os of a device                     |
|                              | `char_node_gpu`                            | Information about the gpu of a device                    |

## Docker Images
All the custom Docker Images are uploaded to Dockerhub:

* Characterization agent can be found <a href="https://hub.docker.com/repository/docker/gkorod/char-agent/general">here </a>
* Kubervirt exporter can be found <a href="https://hub.docker.com/repository/docker/gkorod/kubevirt_exporter/general"> here </a>
* monitoringAPI can be found <a href="https://hub.docker.com/repository/docker/gkorod/monitoringapi/general"> here </a>

## Cite Us

If you use the above code for your research, please cite our paper:

- [EdgeCloud Mon: A lightweight monitoring stack for K3s clusters](https://www.sciencedirect.com/science/article/pii/S2352711024000463)
       
      @article{korontanis2024edgecloud,
      title={EdgeCloud Mon: A lightweight monitoring stack for K3s clusters},
      author={Korontanis, Ioannis and Makris, Antonios and Tserpes, Konstantinos},
      journal={SoftwareX},
      volume={26},
      pages={101675},
      year={2024},
      publisher={Elsevier}
      }
