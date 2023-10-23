# set base image (host OS)
FROM ubuntu:18.04

# set the working directory in the container
ADD . /kubevirt_exporter/

# install dependencies

RUN apt-get update && apt-get install -y \
python3-pip && apt-get install -y git

RUN pip3 install \
prometheus-client \
git+https://github.com/kubevirt/client-python.git \
pyyaml \
kubernetes



EXPOSE 9999
# command to run on container start
CMD [ "python3", "/kubevirt_exporter/main.py" ]
