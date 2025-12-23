# ==============================================================================
# Service: Physics Guard (Docker Image)
# Revision: 1.2.0 (Folder Structure Fix)
# ==============================================================================

FROM python:3.9-slim

WORKDIR /app

# 1. Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Logic
# This command failed before because 'src/' didn't exist. 
# Now that you created it, this will work.
COPY src/ ./src/

# 3. Execution
CMD ["python", "-u", "src/main.py"]
