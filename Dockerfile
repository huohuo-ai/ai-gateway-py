FROM python:3.11-slim

WORKDIR /app

# Configure Alibaba Cloud mirror for faster apt downloads in China
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Copy application code
COPY app/ ./app/

# Copy config
COPY config.yaml.example ./config.yaml

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "app.main"]
