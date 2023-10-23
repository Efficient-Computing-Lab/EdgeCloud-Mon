# Char-agent container

The characterization agent is a custom exporter deployed on
every node in a Kubernetes cluster. This agent is able to find the
location of the node in matters of city, country, continent, latitude
and longitude. In addition, it is capable of ultimately distinguishing
whether the host system is a physical machine or a virtual machine.
It is also capable to describe the model of the CPU along with
its architecture, bits and cores. Additionally it exports the total
size of RAM and the total size of disk. It could also identify the
operating system and report it to Prometheus along with its version.
Among its most noteworthy features is its ability to determine
whether a device includes a battery or contains a GPU.

![alt text](Characterization%20agent.png)
## Build image


```bash
cd characterization-agent
docker buildx build --platform linux/arm/v7,linux/arm64/v8,linux/amd64 -t gkorod/char-agent:v1.0 --push .

```
