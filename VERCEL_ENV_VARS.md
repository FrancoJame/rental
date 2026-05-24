# Required Vercel Environment Variables

Set these in: Vercel Dashboard → Your Project → Settings → Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key (generate a new one!) | `django-insecure-...` |
| `DEBUG` | Always `False` in production | `False` |
| `ALLOWED_HOSTS` | Your Vercel domain | `dreamhouse-ug.vercel.app` |
| `DATABASE_URL` | PostgreSQL connection string (Neon/Supabase) | `postgresql://user:pass@host/db` |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name | `dj7y4rbj6` |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key | `816875948945751` |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API secret | `UUUeZ0...` |
| `EMAIL_HOST_USER` | Gmail address | `frankjames256@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (NOT your real password!) | `xxxx xxxx xxxx xxxx` |
| `DEFAULT_FROM_EMAIL` | From address for emails | `noreply@dreamhouse.ug` |
| `ADMIN_EMAIL` | Admin notification email | `mutebifrancis33@gmail.com` |

## How to generate a Gmail App Password
1. Go to myaccount.google.com
2. Security → 2-Step Verification (must be ON)
3. Security → App Passwords
4. Select app: Mail, device: Other → name it "DreamHouse"
5. Copy the 16-character password into `EMAIL_HOST_PASSWORD`

## How to generate a new SECRET_KEY
Run this in Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
