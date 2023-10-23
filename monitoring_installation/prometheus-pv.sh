echo $1
cd $1/Prometheus
mkdir prometheus
chmod -R 777 prometheus
cd ..
chown -R 1000:0 $1/Prometheus/prometheus/
