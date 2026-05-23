import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import LandlordProfile, EmailVerification

User = get_user_model()

username = 'XaviAlonso'
email = 'francis256james@gmail.com'
first_name = 'Xavi'
last_name = 'Alonso'
password = 'Xavi@uga256'
nin = '1234567890123'

# Check for existing user
existing = User.objects.filter(username=username) | User.objects.filter(email=email)
if existing.exists():
    u = existing.first()
    print('User already exists with id:', u.id)
    ev = None
    try:
        ev = u.email_verification
    except Exception:
        ev = None
    if ev:
        print('Existing verification code (may be expired):', ev.code)
    else:
        ev = EmailVerification.objects.create(user=u)
        print('Created verification record for existing user. Code:', ev.generate_code())
else:
    u = User.objects.create(username=username, email=email, first_name=first_name, last_name=last_name, role=User.LANDLORD)
    u.set_password(password)
    u.save()
    profile, _ = LandlordProfile.objects.get_or_create(user=u)
    profile.national_id_number = nin
    profile.save(update_fields=['national_id_number'])
    ev = EmailVerification.objects.create(user=u)
    code = ev.generate_code()
    print('Created user id:', u.id)
    print('Verification code:', code)

print('Open the following to enter the code in the browser:')
print(f'http://127.0.0.1:8000/verify-email/{u.id}/')
