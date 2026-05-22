FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PATH=/app/.local/bin:$PATH
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
ENTRYPOINT ["sh", "-lc", "gunicorn --bind 0.0.0.0:${PORT:-8000} housing_project.wsgi:application"]
