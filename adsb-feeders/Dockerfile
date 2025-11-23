# Base image for Python applications (Using standard Docker Hub image)
# This is stable and Balena's builder handles the cross-compilation wrapper correctly.
FROM python:3.11-slim 

# Set the working directory
WORKDIR /usr/src/app

# Install Python dependencies
COPY requirements.txt .
# Install build tools necessary for installing some Python libraries (like C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies (primarily 'requests')
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python scripts
# These files pull data from readsb and OpenSky and push it to InfluxDB.
COPY readsb_feeder.py .
COPY readsb_position_feeder.py .
COPY opensky_feeder.py .

# Command to run the three feeder scripts in parallel using run.sh
# Creates a simple script to start all three data ingestion processes simultaneously.
RUN echo '#!/bin/bash\n\
python readsb_feeder.py &\n\
python readsb_position_feeder.py &\n\
python opensky_feeder.py &\n\
wait -n' > run.sh
RUN chmod +x run.sh

# Start the scripts
CMD ["./run.sh"]
