# Use a small, standard Linux base
FROM debian:bookworm-slim

# Install GPSD and the tools you need for testing (gpsmon, ppstest)
RUN apt-get update && apt-get install -y \
    gpsd \
    gpsd-clients \
    pps-tools \
    && rm -rf /var/lib/apt/lists/*

# Expose the GPS data port
EXPOSE 2947

# Start GPSD in foreground (-N) and listen globally (-G)
# The device (/dev/ttyAMA0) comes from the command line args in docker-compose
ENTRYPOINT ["/usr/sbin/gpsd", "-N", "-G"]
