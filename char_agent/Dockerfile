FROM python:3.6.9-slim

RUN mkdir /characterization-agent
WORKDIR /characterization-agent
ADD . /characterization-agent/

RUN apt-get update && apt-get install -y \
pciutils \
virt-what \
python3-pip

RUN pip3 install \
py-cpuinfo \
ipify \
prometheus-client \
psutil

ENV DISPLAY :0.0
EXPOSE 5001
CMD ["python3","/characterization-agent/Prometheus.py"]
