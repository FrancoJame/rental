# Django Housing Project Deployment Guide

## Prerequisites
- Python 3.8+
- pip package manager
- Environment variables configured

## Pre-Deployment Checklist

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and update with your settings:
```bash
cp .env.example .env
```

**Required environment variables:**
- `DEBUG=False` - Must be False in production
- `SECRET_KEY` - Generate a new secure key: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `ALLOWED_HOSTS` - Comma-separated list of your domain(s)

### 3. Database Migration
```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## Deployment Options

### Option A: Heroku Deployment

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Add PostgreSQL: `heroku addons:create heroku-postgresql:hobby-dev`
5. Set environment variables:
   ```bash
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```
6. Deploy: `git push heroku main`

### Option B: Traditional Server (VPS)

#### Using Gunicorn + Nginx

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create systemd service file** at `/etc/systemd/system/gunicorn-housing.service`:
   ```ini
   [Unit]
   Description=Gunicorn daemon for housing project
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/Housing
   ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind unix:/run/gunicorn.sock housing_project.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Start service:**
   ```bash
   sudo systemctl enable gunicorn-housing
   sudo systemctl start gunicorn-housing
   ```

4. **Configure Nginx** to proxy requests to Gunicorn

#### Using Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "housing_project.wsgi"]
```

Build and run:
```bash
docker build -t housing:latest .
docker run -p 8000:8000 housing:latest
```

## Post-Deployment

1. **Verify static files** are being served correctly
2. **Test media uploads** - ensure media folder is writable
3. **Monitor logs** for any errors
4. **Set up regular backups** for your database
5. **Configure email** for password reset functionality (update EMAIL settings in .env)

## Security Reminders

✓ DEBUG is set to False
✓ SECRET_KEY is from environment (not hardcoded)
✓ ALLOWED_HOSTS is restricted to your domain(s)
✓ SECURE_SSL_REDIRECT is enabled
✓ Cookies are secure (HTTPS only)
✓ CSRF protection is enabled

## Troubleshooting

**Static files not loading:**
```bash
python manage.py collectstatic --clear --noinput
```

**Permission denied on media folder:**
```bash
sudo chown -R www-data:www-data /path/to/media
```

**Database migration errors:**
```bash
python manage.py showmigrations
python manage.py migrate --verbosity 2
```

## Support
For more information, see [Django Deployment Checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
