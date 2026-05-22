# Quick Start Guide for Housing Project

## 🆕 NEW FEATURES (May 2026)

### Email Verification System
- Users must verify email with 6-digit code after registration
- Verification codes sent to registered email
- Admin notifications sent to mutebifrancis33@gmail.com
- Users cannot add listings until email is verified

### NIN Registration Field
- All new landlords must provide National ID Number (NIN)
- NIN is unique and required
- Stored in user profile for verification

### Android Compatibility Fixes
- Fixed form submission issues on Android devices
- Better error handling and validation
- File size and type validation
- Double-submission prevention

---

## Local Development Setup

### 1. Clone & Install
```bash
git clone <repository-url>
cd Housing
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

For local development, your `.env` should look like:
```
DEBUG=True
SECRET_KEY=django-insecure-test-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1

# NEW: Email Configuration (Required for new features)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@dreamhouse.ug
ADMIN_EMAIL=mutebifrancis33@gmail.com
```

### 2a. Email Setup (NEW - Required!)

**For Gmail:**
1. Enable 2-factor authentication on your Gmail account
2. Go to: https://myaccount.google.com/apppasswords
3. Select: App = Mail, Device = Windows Computer
4. Copy the generated password
5. Add to .env: `EMAIL_HOST_PASSWORD=your-generated-password`

**For Other Email Services:**
Contact your email provider for SMTP settings

### 3. Initialize Database (⚠️ NEW: Must run migrations for new features)
```bash
# REQUIRED for new email verification and NIN features:
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000

Admin: http://localhost:8000/admin

### 5. Create Test Listings (Optional)
```bash
python manage.py shell
```

Then in the Python shell:
```python
from django.contrib.auth.models import User
from listings.models import Listing

# Create a test user
user = User.objects.create_user(
    username='testlord',
    email='test@example.com',
    password='testpass123'
)

# Create a test listing
listing = Listing.objects.create(
    landlord=user,
    title='Beautiful 2-Bedroom in Kampala',
    room_type='double',
    price_per_month=800000,
    location='Kampala, Uganda',
    telephone='+256789000000',
    description='Spacious rooms with modern amenities',
    in_gate=True,
    inner_bathroom=True
)
```

## Project Structure
- `housing_project/` - Main Django project settings
- `listings/` - Main app with models, views, and forms
- `media/` - User-uploaded images
- `static/` - CSS, JS, images (collected during deployment)

## Common Commands

```bash
# Run migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Collect static files (for production)
python manage.py collectstatic

# Run tests
python manage.py test

# Access shell
python manage.py shell
```

## Troubleshooting

**Port already in use:**
```bash
python manage.py runserver 8001
```

**Database errors:**
```bash
python manage.py migrate --noinput
```

**Missing static files:**
```bash
python manage.py collectstatic --clear --noinput
```

For more details, see [DEPLOYMENT.md](DEPLOYMENT.md)
