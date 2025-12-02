cat > telegraf-agent/Dockerfile << 'EOF'
FROM telegraf:1.30
# Basic Config Generation (Stripped of GPS scripts)
RUN echo '[global_tags]' > /etc/telegraf/telegraf.conf && \
    echo '  role = "sensor-node"' >> /etc/telegraf/telegraf.conf && \
    echo '  location = "EFHK-Corridor"' >> /etc/telegraf/telegraf.conf && \
    echo '[agent]' >> /etc/telegraf/telegraf.conf && \
    echo '  interval = "15s"' >> /etc/telegraf/telegraf.conf && \
    echo '  hostname = "RPi4-Sensor"' >> /etc/telegraf/telegraf.conf && \
    echo '[[outputs.influxdb]]' >> /etc/telegraf/telegraf.conf && \
    echo '  urls = ["http://192.168.1.134:8086"]' >> /etc/telegraf/telegraf.conf && \
    echo '  database = "readsb"' >> /etc/telegraf/telegraf.conf && \
    echo '[[inputs.cpu]]' >> /etc/telegraf/telegraf.conf && \
    echo '  percpu = true' >> /etc/telegraf/telegraf.conf && \
    echo '  totalcpu = true' >> /etc/telegraf/telegraf.conf && \
    echo '[[inputs.mem]]' >> /etc/telegraf/telegraf.conf && \
    echo '[[inputs.temp]]' >> /etc/telegraf/telegraf.conf && \
    echo '[[inputs.disk]]' >> /etc/telegraf/telegraf.conf && \
    echo '  ignore_fs = ["tmpfs", "devtmpfs", "overlay", "aufs"]' >> /etc/telegraf/telegraf.conf
CMD ["telegraf"]
EOF
