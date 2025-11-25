# Use a clean, slim Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies first (for caching)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ .

# Run the application
CMD ["python", "main.py"]
