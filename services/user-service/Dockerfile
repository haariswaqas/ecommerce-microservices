FROM python:3.12-alpine

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Don't run as root in production
RUN adduser --disabled-password appuser
USER appuser

EXPOSE 8001