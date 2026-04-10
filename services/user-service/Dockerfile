FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password appuser

# Collect static files before switching to non-root user
RUN python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000
CMD ["gunicorn", "user_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]