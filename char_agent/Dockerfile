FROM python:3.11-slim-bullseye

# Build-time argument (default: generic)
ARG TARGET=generic
ENV TARGET=${TARGET}



RUN apt-get update && apt-get install -y \
    pciutils virt-what python3-pip gnat sudo gprbuild git systemd

# Install Python dependencies (common)
RUN pip3 install \
    py-cpuinfo \
    prometheus-client \
    psutil \
    requests \
    python-dotenv \
    pandas

RUN mkdir /characterization-agent
WORKDIR /characterization-agent
COPY . /characterization-agent

# Conditional installs
RUN if [ "$TARGET" = "jetson" ]; then \
        cp /characterization-agent/jetson/* /characterization-agent/ && \
        pip3 install jetson-stats && \
        echo "Building for Jetson device"; \
    elif [ "$TARGET" = "rpi" ]; then \
        echo "Building for Raspberry Pi" && \
        cp /characterization-agent/other_machines/* /characterization-agent/ && \
        git clone https://github.com/joular/powerjoular.git && \
        cp /characterization-agent/install-powerjoular.sh powerjoular/installer/ && \
        cd powerjoular/installer && ./install-powerjoular.sh; \
    else \
        echo "Building for generic Linux" && \
        cp /characterization-agent/other_machines/* /characterization-agent/ && \
        git clone https://github.com/joular/powerjoular.git && \
        cp /characterization-agent/install-powerjoular.sh powerjoular/installer/ && \
        cd powerjoular/installer && ./install-powerjoular.sh; \
    fi


ENV DISPLAY=:0.0
EXPOSE 5001

CMD ["python3", "/characterization-agent/Prometheus.py"]
