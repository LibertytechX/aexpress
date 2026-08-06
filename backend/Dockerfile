# Use official Python image matching virtualenv version
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/py/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        binutils \
        postgresql-client \
        libpq-dev \
        build-essential \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install application and testing dependencies
RUN pip install --upgrade pip "setuptools<81" wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-django pytest-mock factory-boy responses freezegun pytest-cov pytest-timeout

# Copy project code
COPY . /app/

# Expose port
EXPOSE 8000
