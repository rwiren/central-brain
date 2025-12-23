# ==============================================================================
# Service: ADSB-Feeders (Docker Image)
# Revision: 2.2.0 (Fix: Added InfluxDB Client)
# Date:     2025-12-05
# Description: 
#   Runs data collectors and logic engines for the Central Brain.
# ==============================================================================

FROM python:3.9-slim

WORKDIR /app

# 1. Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Scripts
COPY . .

# 3. Permissions
RUN chmod +x run.sh

# 4. Execution
# -u forces unbuffered stdout so logs appear instantly in Dashboard
CMD ["/bin/bash", "run.sh"]
