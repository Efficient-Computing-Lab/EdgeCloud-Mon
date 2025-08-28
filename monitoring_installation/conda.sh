#!/bin/bash

# Check the architecture (x86_64 or ARM)
ARCH=$(uname -m)

# Define the path for the architecture-specific requirements.txt files


if [[ "$ARCH" == "x86_64" ]]; then
    # For x86_64 architecture (Intel/AMD)
    echo "Detected x86_64 architecture. Installing Miniconda for x86_64."
    MINICONDA_INSTALLER="Miniconda3-latest-Linux-x86_64.sh"
elif [[ "$ARCH" == "aarch64" ]]; then
    # For ARM architecture (ARM 64-bit, e.g., Raspberry Pi)
    echo "Detected ARM architecture. Installing Miniconda for ARM."
    MINICONDA_INSTALLER="Miniconda3-latest-Linux-aarch64.sh"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

# Download Miniconda installer
echo "Downloading Miniconda installer..."
wget "https://repo.anaconda.com/miniconda/$MINICONDA_INSTALLER"

# Install Miniconda to /opt
echo "Installing Miniconda to /opt..."
sudo bash "$MINICONDA_INSTALLER" -b -p /opt/miniconda3

# Source the conda.sh script to initialize Conda in the current shell
echo "Initializing Conda..."
source /opt/miniconda3/etc/profile.d/conda.sh

# Add Conda-Forge channel for package installation
conda config --add channels conda-forge
conda config --set channel_priority strict

# Create a conda environment with Python 3.11
echo "Creating Conda environment with Python 3.11..."
conda create --name profiling python=3.11 -y

# Activate the environment
echo "Activating the conda environment 'monitoring-installation'..."
conda activate monitoring-installation

# Install dependencies from the appropriate requirements.txt
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r requirements.txt

# Verify installed packages
echo "Verifying installed packages..."
pip list

# Optionally deactivate the environment when done
#echo "Deactivating the environment..."
#conda deactivate

# Clean up the installer
echo "Cleaning up the installer..."
rm "$MINICONDA_INSTALLER"

echo "Miniconda installation and environment setup complete!"