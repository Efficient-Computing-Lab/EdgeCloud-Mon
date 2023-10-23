import yaml
import os
from pathlib import Path


def characterization_agent(gpu_list):
    kubernetes = {
        "apiVersion": "apps/v1",
        "kind": "DaemonSet",
        "metadata": {
            "name": "char-agent",
            "namespace": "monitoring",
            "labels": {
                "app": "char-agent"
            }
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": "char-agent"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "char-agent"
                    }
                },
                "spec": {
                    "hostNetwork": True,
                    "containers": [
                        {
                            "name": "char-agent",
                            "image": "gkorod/char-agent:v1.0",
                            "imagePullPolicy": "Always",
                            "securityContext": {
                                "privileged": True
                            },
                            "env": [
                                {
                                    "name": "NODE_NAME",
                                    "valueFrom": {
                                        "fieldRef": {
                                            "fieldPath": "spec.nodeName"
                                        }
                                    }
                                },
                                {"name": "GPU_LIST", "value": str(gpu_list)}
                            ],
                            "ports": [
                                {
                                    "containerPort": 5001,
                                    "name": "char-agent"
                                }
                            ]
                        }
                    ],
                    "imagePullSecrets": [
                        {
                            "name": "charagent"
                        }
                    ]
                }
            }
        }
    }
    with open('manifests/characterization-agent/char-agentDeployment.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def monitoring_api(echoserver_ip, rid_ip, prometheus_ip, master_ip, minicloud_id):
    kafka_ip = 'continuum.accordion-project.eu:9092'

    kubernetes = {'apiVersion': 'apps/v1',
                  'kind': 'Deployment',
                  'metadata': {
                      'name': 'monitoring-api',
                      'namespace': 'monitoring', 'labels': {'app': 'monitoring-api'}},
                  'spec': {'selector': {'matchLabels': {'app': 'monitoring-api'}},
                           'template': {'metadata': {'labels': {'app': 'monitoring-api'}},
                                        'spec': {'hostNetwork': True, 'containers': [
                                            {'name': 'monitoring-api',
                                             'image': 'gkorod/monitoringapi:v1.0',
                                             'imagePullPolicy': 'Always',
                                             'env': [{'name': 'ECHOSERVER_IP', 'value': echoserver_ip},
                                                     {'name': 'MASTER_IP', 'value': master_ip},
                                                     {'name': 'KAFKA_IP', 'value': kafka_ip},
                                                     {'name': 'RID_IP', 'value': rid_ip},
                                                     {'name': 'PROMETHEUS_IP', 'value': prometheus_ip},
                                                     {'name': 'MINICLOUD_ID', 'value': minicloud_id}],
                                             'volumeMounts': [{'name': 'config', 'mountPath': '/root/'}]}],
                                                 'volumes': [
                                                     {'name': 'config',
                                                      'hostPath': {'path': os.getcwd() + '/config',
                                                                   'type': 'Directory'}}],
                                                 'nodeSelector': {'beta.kubernetes.io/os': 'linux',
                                                                  'monitoringMaster': 'true'},
                                                 'imagePullSecrets': [{'name': 'api'}]}}}}
    with open('monitoringAPI-Deployment.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def alert_webhook(prometheus_ip, minicloud_id):
    kafka_ip = 'continuum.accordion-project.eu:9092'
    kubernetes = {'apiVersion': 'apps/v1',
                  'kind': 'Deployment',
                  'metadata': {
                      'name': 'alert-webhook',
                      'namespace': 'monitoring', 'labels': {'app': 'alert-webhook'}},
                  'spec': {'selector': {'matchLabels': {'app': 'alert-webhook'}},
                           'template': {'metadata': {'labels': {'app': 'alert-webhook'}},
                                        'spec': {'hostNetwork': True, 'containers': [
                                            {'name': 'alert-webhook',
                                             'image': 'gkorod/alert_webhook:v1.0',
                                             'imagePullPolicy': 'Always',
                                             'env': [{'name': 'KAFKA_IP', 'value': kafka_ip},
                                                     {'name': 'PROMETHEUS_IP', 'value': prometheus_ip},
                                                     {'name': 'MINICLOUD_ID', 'value': minicloud_id}]
                                             }],

                                                 'nodeSelector': {'beta.kubernetes.io/os': 'linux',
                                                                  'monitoringMaster': 'true'},
                                                 'imagePullSecrets': [{'name': 'alert'}]}}}}
    with open('alert-webhook-Deployment.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def kubevirt_exporter(ip):
    kubernetes = {'apiVersion': 'apps/v1',
                  'kind': 'Deployment',
                  'metadata': {
                      'name': 'kubevirt-exporter',
                      'namespace': 'monitoring', 'labels': {'app': 'kubevirt-exporter'}},
                  'spec': {'selector': {'matchLabels': {'app': 'kubevirt-exporter'}},
                           'template': {'metadata': {'labels': {'app': 'kubevirt-exporter'}},
                                        'spec': {'containers': [
                                            {'name': 'kubevirt-exporter',
                                             'image': 'gkorod/kubevirt_exporter:v1.0',
                                             'env': [{'name': 'IP', 'value': ip}],
                                             'imagePullPolicy': 'IfNotPresent',
                                             'ports': [{'containerPort': 9999, 'name': 'metrics'}],
                                             'volumeMounts': [{'name': 'config',
                                                               'mountPath': '/root/'}]}],
                                            'volumes': [
                                                {'name': 'config',
                                                 'hostPath': {'path': os.getcwd() + '/config', 'type': 'Directory'}}],
                                            'nodeSelector': {'beta.kubernetes.io/os': 'linux',
                                                             'monitoringMaster': 'true'},
                                            'imagePullSecrets': [{'name': 'kubevirt-exporter-secret'}]}}}}
    with open('manifests/kubevirt-exporter/kubevirt-exporter-deployment.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def alertmanager_secret(ip):
    ip = 'http://' + ip + ':3000/webhook'
    stringData = {'global': {'resolve_timeout': '5m'},
                  'inhibit_rules': [{'equal': ['namespace', 'alertname'], 'source_match': {'severity': 'critical'},
                                     'target_match_re': {'severity': 'warning|info'}},
                                    {'equal': ['namespace', 'alertname'], 'source_match': {'severity': 'warning'},
                                     'target_match_re': {'severity': 'info'}}],
                  'receivers': [{'name': 'webhook', 'webhook_configs': [{'url': ip, 'send_resolved': True}]}],
                  'route': {'group_by': ['namespace'], 'group_interval': '5m', 'group_wait': '30s',
                            'receiver': 'webhook', 'repeat_interval': '12h',
                            'routes': [{'match': {'alertname': 'Watchdog'}, 'receiver': 'webhook'},
                                       {'match': {'severity': 'critical'}, 'receiver': 'webhook'}]}}

    kubernetes = {'apiVersion': 'v1', 'data': '', 'kind': 'Secret',
                  'metadata': {'name': 'alertmanager-main', 'namespace': 'monitoring'},
                  'stringData': {'alertmanager.yaml': stringData}, 'type': 'Opaque'}

    with open('manifests/alert-manager/alertmanager-secret.yaml', 'w') as file:
        yaml.dump(kubernetes, file, default_style=False)
    with open('manifests/alert-manager/alertmanager-secret.yaml', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    i = 0
    for line in data:
        if "data: ''" in line:
            data[i] = 'data: {} \n'
        if 'alertmanager.yaml:' in line:
            data[i] = '  alertmanager.yaml: |- \n'
        i = i + 1
    with open('manifests/alert-manager/alertmanager-secret.yaml', 'w') as file:
        file.writelines(data)


def prometheus_kubeControllerManager_DiscoveryEndpoints(ip):
    kubernetes = {
        'apiVersion': 'v1',
        'kind': 'Endpoints',
        'metadata': {'labels': {'k8s-app': 'kube-controller-manager-prometheus-discovery'},
                     'name': 'kube-controller-manager-prometheus-discovery',
                     'namespace': 'kube-system'},
        'subsets': [{'addresses': [{'ip': ip}], 'ports': [{'name': 'http-metrics', 'port': 10252, 'protocol': 'TCP'}]}]
    }
    with open('manifests/prometheus/prometheus-kubeControllerManagerPrometheusDiscoveryEndpoints.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def prometheus_kubeControllerScheduler_DiscoveryEndpoints(ip):
    kubernetes = {
        'apiVersion': 'v1',
        'kind': 'Endpoints',
        'metadata': {'labels': {'k8s-app': 'kube-scheduler-prometheus-discovery'},
                     'name': 'kube-scheduler-prometheus-discovery',
                     'namespace': 'kube-system'},
        'subsets': [{'addresses': [{'ip': ip}], 'ports': [{'name': 'http-metrics', 'port': 10251, 'protocol': 'TCP'}]}]
    }
    with open('manifests/prometheus/prometheus-kubeControllerSchedulerPrometheusDiscoveryEndpoints.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def pv(path, name, cwd):
    write_path = cwd + '/' + name + '-volume.yaml'
    kubernetes = {'apiVersion': 'v1',
                  'kind': 'PersistentVolume',
                  'metadata': {'name': name + '-pv-volume', 'labels': {'type': 'local'}},
                  'spec': {'storageClassName': 'local-path', 'capacity': {'storage': '10Gi'},
                           'accessModes': ['ReadWriteOnce'],
                           'persistentVolumeReclaimPolicy': 'Retain',
                           'hostPath': {'path': path}}}

    with open(write_path, 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)


def prometheus_ingress(ip):
    ip = 'prometheus.' + ip + '.nip.io'
    kubernetes = {
        'apiVersion': 'extensions/v1beta1',
        'kind': 'Ingress',
        'metadata': {'name': 'prometheus-k8s', 'namespace': 'monitoring',
                     'annotations': {'kubernetes.io/ingress.class': 'traefik',
                                     'ingress.kubernetes.io/auth-type': "basic",
                                     'ingress.kubernetes.io/auth-secret': "prometheus-auth"}},
        'spec': {
            'rules': [{'host': ip, 'http': {
                'paths': [{'backend': {'serviceName': 'prometheus-k8s', 'servicePort': 'web'}, 'path': '/'}]}}],
            'tls': [{'hosts': [ip]}]}}
    with open('manifests/ingress-prometheus.yaml', 'w') as outfile:
        yaml.dump(kubernetes, outfile, default_flow_style=False)
