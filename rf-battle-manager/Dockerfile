# ------------------------------------------------------------------------------
# Service: RF Battle Manager (Aggregator)
# Revision: 1.0.0 (2025-12-04)
# Location: Central Brain (RPi5)
# Description: Polls remote RPi4 nodes and pushes calculated stats to InfluxDB.
# ------------------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# We create requirements.txt inline to keep the directory clean
RUN echo "requests" > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Application Logic
COPY src/main.py .

# Run unbuffered to see logs in Balena Dashboard immediately
CMD ["python", "-u", "main.py"]
