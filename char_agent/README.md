# Char-agent container

The characterization agent is a custom exporter deployed on
every node in a Kubernetes cluster. In version 1.1, this agent is able to find the
location of the node in matters of city, country, continent, latitude
and longitude. In addition, it is capable of ultimately distinguishing
whether the host system is a physical machine or a virtual machine.
It is also capable to describe the model of the CPU along with
its architecture, bits, cores and energy consumption. Additionally it exports the total
size of RAM and the total size of disk. It could also identify the
operating system and report it to Prometheus along with its version.
Among its most noteworthy features is its ability to determine
whether a device includes a battery or contains a GPU.

The CPU energy consumption metric is only present in v1.1 anv v1.2 and is being retrieved by [Powerjoular](https://github.com/joular/powerjoular)

![alt text](Characterization%20agent.png)
## Build image
RPi and Jetson devices do not have a common library to measure CPU energy consumption. For that reason
this monitoring solution provides two different Docker images of characacterization agents.

### RPi and X86 Docker images
```bash
cd characterization-agent
docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64/v8 --build-arg TARGET=rpi -t gkorod/char-agent:v1.2 --push .
docker run  -d --name char-agent -p 5001:5001 --env-file /opt/char-agent/.env gkorod/char-agent:v1.2
docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64/v8 -t gkorod/char-agent:v1.2 --push .
docker run  -d --name char-agent -p 5001:5001 --env-file /opt/char-agent/.env gkorod/char-agent:v1.2
```

### Jetson Docker images
```bash
cd characterization-agent
docker buildx build --platform linux/arm/v7,linux/arm64/v8 --build-arg TARGET=jetson -t gkorod/char-agent:v1.2-jetson --push .
docker run  -d --name char-agent -p 5001:5001 -v /run/jtop.sock:/run/jtop.sock --env-file /opt/char-agent/.env gkorod/char-agent:v1.2-jetson
```
