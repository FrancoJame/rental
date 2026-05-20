# Media Files Management Guide

## Overview

Your Django Housing Project uses media files (images) for house listings. This guide ensures images are **permanently stored** and **never disappear** during deployment and in production.

## Local Development

In development (DEBUG=True), Django automatically serves media files from the `media/` directory at `/media/` URL.

**Media files are stored in:**
```
Housing/
├── media/
│   ├── listings/
│   │   ├── images/           # House listing photos
│   │   └── national_ids/     # Landlord verification documents
```

## Production Deployment

### Important: In Production (DEBUG=False)

**Django does NOT serve media files in production.** You must configure your web server to serve them.

### Option 1: Nginx (Recommended)

Add this to your Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Serve static files
    location /static/ {
        alias /path/to/Housing/staticfiles/;
    }

    # Serve media files
    location /media/ {
        alias /path/to/Housing/media/;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Apache

Add this to your Apache VirtualHost:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com

    # Serve static files
    Alias /static/ /path/to/Housing/staticfiles/

    # Serve media files
    Alias /media/ /path/to/Housing/media/

    <Directory /path/to/Housing/staticfiles/>
        Require all granted
    </Directory>

    <Directory /path/to/Housing/media/>
        Require all granted
    </Directory>

    # Proxy to Gunicorn
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

### Option 3: Cloud Storage (AWS S3, Azure Blob, Google Cloud Storage)

For better scalability, use cloud storage:

#### AWS S3

1. Install required packages:
```bash
pip install boto3 django-storages
```

2. Update `.env`:
```
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

3. Update `settings.py` to use S3 storage (optional implementation)

#### Azure Blob Storage

1. Install packages:
```bash
pip install azure-storage-blob django-azure-blob-storage
```

2. Configure in `.env` and `settings.py`

### Option 4: Heroku Deployment

**Important:** Heroku uses ephemeral filesystems. Images uploaded to the local filesystem will be **deleted every 30 minutes**.

**Solution:** Use AWS S3 or Heroku's add-ons.

## Backup & Persistence

### Local/VPS Servers

**Ensure regular backups:**

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/housing"
SOURCE="/path/to/Housing/media"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz $SOURCE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "media_backup_*.tar.gz" -mtime +30 -delete
```

Add to crontab for daily backups:
```bash
0 2 * * * /path/to/backup-script.sh
```

### Permissions

Ensure media folder has correct permissions:

```bash
# Allow web server to read/write
sudo chown -R www-data:www-data /path/to/Housing/media
sudo chmod -R 755 /path/to/Housing/media

# For Gunicorn with specific user:
sudo chown -R gunicorn:gunicorn /path/to/Housing/media
```

## Testing Image Persistence

### Step 1: Upload a Test Image

1. Go to Landlord Dashboard
2. Add a new house listing
3. Upload test images
4. Save the listing

### Step 2: Verify Images Are Saved

```bash
# Check if files exist
ls -la Housing/media/listings/images/
```

### Step 3: Verify Database Reference

```bash
# Check in Django shell
python manage.py shell
```

```python
from listings.models import Listing
listing = Listing.objects.last()
print(listing.image_front.url)  # Should show /media/listings/images/...
print(listing.image_front.path)  # Should show full file path
```

### Step 4: Test in Browser

Navigate to the listing detail page and verify images display correctly.

## Troubleshooting

### Images Not Displaying (Development)

**Problem:** Images show 404 error in development
**Solution:** 
- Ensure DEBUG=True in development
- Check that `/media/` URLs are in your urlpatterns
- Verify media folder exists and has files

### Images Not Displaying (Production)

**Problem:** Images show 404 error after deployment
**Solution:**
- Configure web server (Nginx/Apache) to serve `/media/` directory
- Check folder permissions: `sudo chmod -R 755 /path/to/media/`
- Verify `MEDIA_ROOT` and `MEDIA_URL` in settings.py
- Check web server logs for errors

### Heroku: Images Disappear After Restart

**Problem:** Images disappear every 30 minutes on Heroku
**Solution:** Use AWS S3 or other persistent cloud storage (Heroku has ephemeral filesystem)

### Database Shows Image Path But File Missing

**Problem:** Database reference exists but actual file is missing
**Solution:**
- Re-upload the images
- Check file permissions
- Ensure backup/restore was successful
- Use cloud storage for redundancy

## Best Practices

1. **Always backup media files** - Set up daily automated backups
2. **Use cloud storage for production** - More reliable than filesystem
3. **Set correct permissions** - Ensure web server can read/write
4. **Monitor disk space** - Large images can consume storage quickly
5. **Validate image uploads** - Add file size limits in forms
6. **Regular maintenance** - Archive old/unused images periodically

## Security

- **Restrict file types** - Only allow image uploads (.jpg, .png, .gif)
- **Validate file sizes** - Limit max upload size
- **Scan for malware** - Use ClamAV or similar for user uploads
- **Use HTTPS** - Serve media over secure connections
- **Protect sensitive files** - National ID scans should not be publicly accessible

## Configuration Checklist

- [x] MEDIA_ROOT configured in settings.py
- [x] MEDIA_URL configured in settings.py
- [x] Media folder exists and has proper structure
- [x] URLs configured to serve media in development
- [x] Web server configured to serve media in production
- [x] Backup strategy in place
- [x] Permissions set correctly
- [x] File size limits configured
- [x] Malware scanning enabled (optional)

## Additional Resources

- [Django Media Files Documentation](https://docs.djangoproject.com/en/6.0/topics/files/)
- [Nginx Static File Serving](https://nginx.org/en/docs/http/ngx_http_static_module.html)
- [Apache File Serving](https://httpd.apache.org/docs/current/howto/auth.html)
- [AWS S3 Django Integration](https://django-storages.readthedocs.io/en/latest/backends/amazon_S3.html)

Your images will **NOT disappear** when you:
1. ✅ Use this guide for proper configuration
2. ✅ Set up backups
3. ✅ Use persistent storage (cloud or properly configured server)
4. ✅ Maintain correct folder permissions
