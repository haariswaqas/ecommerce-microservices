# order_service/Dockerfile
FROM python:3.12-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Add non-root user
RUN adduser --disabled-password appuser
USER appuser

# Expose port
EXPOSE 8003

# Run Gunicorn server
CMD ["gunicorn", "order_service.wsgi:application", "--bind", "0.0.0.0:8003", "--workers", "3"]