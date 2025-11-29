# Base image: Lightweight Python 3.11
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Install dependencies
# Note: We explicitly pin paho-mqtt to ensure it works with the new Callback API v2
# We use --no-cache-dir to keep the image size small (best practice for Balena)
RUN pip install --no-cache-dir \
    requests \
    influxdb \
    "paho-mqtt>=2.0.0" \
    geopy

# Copy the source code (main.py) into the container
COPY src/ .

# Run the tracker unbuffered (-u)
# This ensures print() statements show up immediately in the Balena logs
CMD ["python", "-u", "main.py"]

# --- REBUILD TRIGGER ---
# Change the version number below to force Balena to rebuild this container
# Current Version: v2.3 (Fixing MQTT API Crash)
