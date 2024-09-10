# Use Python 3.12 slim image as the base
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY poetry.lock pyproject.toml /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy project files
COPY . /app

# Run the application
CMD ["poetry", "run", "python", "-m", "app.main"]
