# STABILITY FIX: Pin specific version instead of 'latest'
FROM telegraf:1.30

# Install gpsd-clients for 'gpspipe'
RUN apt-get update && apt-get install -y gpsd-clients && rm -rf /var/lib/apt/lists/*

# Copy configuration and scripts
COPY telegraf.conf /etc/telegraf/telegraf.conf
COPY gpsd_telegraf.sh /usr/local/bin/gpsd_telegraf.sh

# Make script executable
RUN chmod +x /usr/local/bin/gpsd_telegraf.sh
