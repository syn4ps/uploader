# Use the official Python image as the base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies with Poetry
RUN poetry install --no-root --no-dev

# Expose the port the app runs on
EXPOSE 18000

# Command to run the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:18000", "--workers", "4", "uploader.wsgi:app"]
