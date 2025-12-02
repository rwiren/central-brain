cat > gps-logger/Dockerfile << 'EOF'
FROM python:3.11-slim
RUN pip install requests
COPY main.py /app/main.py
WORKDIR /app
CMD ["python", "-u", "main.py"]
EOF
