# Base image: Lightweight Python
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies for InfluxDB 1.8 and Geodesic calculations
RUN pip install --no-cache-dir requests influxdb paho-mqtt geopy

# Copy the source code (main.py) into the container
COPY src/ .

# Run the tracker unbuffered (-u) so logs show up instantly in Balena
CMD ["python", "-u", "main.py"]
