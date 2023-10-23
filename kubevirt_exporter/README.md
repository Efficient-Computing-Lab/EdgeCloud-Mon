# Kubevirt Exporter

The Kubevirt exporter interacts with the Kubevirt API to obtain the current status of virtual machines, determining whether they are operational or inactive. For monitoring metrics related to Windows virtual machines, we recommend installing the Windows exporter. Additionally, developers need to define a ServiceMonitor file based on definitions of the labels in the windows-exporter-service.yaml file. This step ensures that Prometheus can automatically identify the new targets for monitoring.

![alt text](Kubevirt%20exporter.png)

 
## Windows exporter detection
In the ACCORDION platform, this exporter is utilized to monitor applications that must be deployed on a machine running a Windows virtual machine. ACCORDION achieves this by deploying Windows virtual machines pre-installed with the Windows exporter and a specific application component using Kubevirt. These virtual machines serve as deployment units for the said application components rather than acting as hosts. Consequently, we only showcase the detection of the Windows exporter, and there isn't an example illustrating the detection of Linux virtual machines deployed via Kubevirt. This is because there was no necessity for such a requirement. As stated on the project's <a href="https://github.com/f-coda/EdgeCloud-Mon/tree/main"> main page </a>, we have already incorporated node exporter and kube-state-metrics for monitoring host and K3s pods, catering to other application components that need to be deployed on Linux hosts.

![alt text](Prometheus%20service%20discovery.png)
## Build image


```bash
cd monitoringapi
docker buildx build --platform linux/arm/v7,linux/arm64/v8,linux/amd64 -t gkorod/kubevirt_exporter:v1.0 --push .

```
