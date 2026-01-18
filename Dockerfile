FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements-api.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY api/ ./api/

# Expose port
EXPOSE 8080

# Run with uvicorn
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]
