import datetime
import json
import queue
import logging
import requests
import time
import threading
from pprint import pprint
import PrometheusInterface
import schedule
from datetime import date
import json
from Kafka_Producer import Producer

q = queue.Queue()


def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


def minicloud_metrics():
    PrometheusInterface.platform_metrics()


def ASR_pod_information():
    PrometheusInterface.pod_information()


def ASR_vm_information():
    PrometheusInterface.vminformation()


def RID_metrics():
    PrometheusInterface.physical_metrics()


def ECHOSERVER():
    type = 'echoserver'
    PrometheusInterface.characterization(type)


def RID_Info():
    type = 'rid'
    PrometheusInterface.characterization(type)


def ACES_metrics():
    PrometheusInterface.disk_metrics()


def RP_pod_metrics():
    PrometheusInterface.virtual_metrics()


def RP_vm_metrics():
    PrometheusInterface.vm_metrics()


def RP_namespace_metrics():
    PrometheusInterface.namespace_metrics()


def Grafana_metrics():
    PrometheusInterface.Grafana_metrics_set()
    PrometheusInterface.Grafana_VM_metrics_set()


schedule.every(30).seconds.do(run_threaded, ECHOSERVER())
schedule.every(30).seconds.do(run_threaded, Grafana_metrics)
schedule.every(60).seconds.do(run_threaded, RID_Info)
schedule.every(30).seconds.do(run_threaded, RID_metrics)
schedule.every(30).seconds.do(run_threaded, ACES_metrics)
schedule.every(60).seconds.do(run_threaded, RP_pod_metrics)
schedule.every(60).seconds.do(run_threaded, RP_vm_metrics)
schedule.every(60).seconds.do(run_threaded, RP_namespace_metrics)
schedule.every(40).seconds.do(run_threaded, ASR_pod_information)
schedule.every(40).seconds.do(run_threaded, ASR_vm_information)
schedule.every(40).seconds.do(run_threaded, minicloud_metrics)
# paper = threading.Thread(target=paper_metrics)
# paper.start()

while True:
    schedule.run_pending()
    time.sleep(1)
