FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI and buildx
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Ensure buildx is available
RUN docker buildx version || echo "buildx will be available at runtime"

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8001

# Run server
CMD uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
