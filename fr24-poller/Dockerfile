# ==============================================================================
# Service: FR24 Poller (Docker Image)
# Revision: 1.1.0 (Dependency Fix)
# ==============================================================================
FROM python:3.9-slim

WORKDIR /app

# 1. Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Logic
COPY src/ .

# 3. Execution
CMD ["python", "-u", "main.py"]
