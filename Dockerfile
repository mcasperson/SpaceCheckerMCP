# Use Python 3.14 as the base image
FROM python:3.14-slim

# Install Node.js (required for npx and @octopusdeploy/mcp-server)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY tools/ ./tools/
COPY messages/ ./messages/
COPY aspects/ ./aspects/

# Set environment variables (these should be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Run the application
ENTRYPOINT ["python", "main.py"]
CMD []

