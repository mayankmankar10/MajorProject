# Multi-stage build for Python backend
FROM python:3.11-slim as backend

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY .env .env

# Copy existing database and vector indexes
# These will be mounted as volumes in production
COPY manpower.db ./manpower.db
COPY backend/db/faiss_indexes/ ./backend/db/faiss_indexes/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
