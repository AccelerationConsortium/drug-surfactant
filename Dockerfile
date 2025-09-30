# Railway deployment configuration
# This file configures the Railway deployment for the drug-surfactant API

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for Opentrons
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py .
COPY api_helper_functions.py .
COPY experiments/ ./experiments/

# Expose the port that the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV OPENTRONS_PROTOCOL_API_VERSION=2.21

# Command to run the application
CMD ["python", "api_server.py"]