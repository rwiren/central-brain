# Use a slim Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

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
