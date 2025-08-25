FROM python:3.11-slim-bullseye

# Create and set the working directory
RUN mkdir /characterization-agent
WORKDIR /characterization-agent

# Copy the current directory contents into the container
COPY . /characterization-agent/

# Update and install necessary packages
RUN apt-get update && apt-get install -y \
    pciutils \
    virt-what \
    python3-pip \
    gnat \
    sudo \
    gprbuild \
    git \
    systemd

# Install Python dependencies
RUN pip3 install \
    py-cpuinfo \
    prometheus-client \
    psutil \
    requests \
    pandas

# Clone the powerjoular repository and run the installer
RUN git clone https://github.com/joular/powerjoular.git
RUN cp /characterization-agent/install-powerjoular.sh powerjoular/installer

RUN cd powerjoular/installer && ./install-powerjoular.sh


# Set environment variable
ENV DISPLAY=:0.0

# Expose the necessary port
EXPOSE 5001

# Define the command to run the application
CMD ["python3", "/characterization-agent/Prometheus.py"]
