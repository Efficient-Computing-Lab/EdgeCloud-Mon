# set base image (host OS)
FROM ubuntu:18.04

# set the working directory in the container
RUN mkdir /data
WORKDIR /monitoringapi
ADD . /monitoringapi/

# install dependencies
RUN apt-get update && apt-get install -y \
python3-pip \
git

RUN pip3 install \
schedule \
oyaml \
requests \
unidecode \
kafka-python==2.0.2 \
git+https://github.com/kubernetes-client/python.git



EXPOSE 4000
# command to run on container start
CMD [ "python3", "/monitoringapi/Controller.py" ]
