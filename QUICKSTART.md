# Quick Start Guide for Housing Project

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
```

### 3. Initialize Database
```bash
python manage.py migrate
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
