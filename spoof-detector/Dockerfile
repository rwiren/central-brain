# Use a slim Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# --- FIX: Install Git and build tools ---
# This prevents "Cannot find command 'git'" errors if requirements need it
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY watchdog.py .

# Python environment variables
# PYTHONUNBUFFERED=1 ensures logs appear in Balena immediately
ENV PYTHONUNBUFFERED=1

# Run the watchdog script
CMD ["python", "watchdog.py"]
