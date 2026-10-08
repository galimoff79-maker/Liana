FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directories
RUN mkdir -p /app/uploads/images \
    /app/uploads/videos \
    /app/uploads/voices \
    /app/uploads/files \
    /app/uploads/avatars

# Expose port
EXPOSE 8000

# Run the application (single worker for WebSocket support)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
