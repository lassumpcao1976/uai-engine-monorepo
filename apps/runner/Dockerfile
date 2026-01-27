FROM python:3.11-slim

# Install Docker CLI (for Docker-in-Docker or Docker socket access)
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/runner/main.py .

# Expose runner port
EXPOSE 8001

CMD ["python", "main.py"]
