FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# --- INSTALL GIT (Required for OpenSky API) ---
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY watchdog.py .
CMD ["python", "watchdog.py"]
