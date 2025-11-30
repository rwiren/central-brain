# File: central-brain/runway-tracker/Dockerfile

# Base image: Lightweight Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install dependencies (CRITICAL: Pinned paho-mqtt version)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code (main.py) into the container
COPY src/main.py .

# Run the tracker unbuffered (-u)
CMD ["python", "-u", "main.py"]

# --- REBUILD TRIGGER ---
# This ensures the new logic and libraries are always compiled.
