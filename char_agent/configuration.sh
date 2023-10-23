apt purge python3.9
apt-get update
apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
apt-get install -y libsqlite3-0
wget https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tar.xz
tar xvf Python-3.6.9.tar.xz
cd Python-3.6.9
./configure --enable-optimizations --enable-loadable-sqlite-extensions
make -j 8
make altinstall
cd ..