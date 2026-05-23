import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import LandlordProfile, EmailVerification

User = get_user_model()
username = f"verifydemo{int(time.time())}"
email = f"{username}@example.com"
password = 'Testpass1!'

user = User.objects.create(username=username, email=email, first_name='Demo', last_name='Verify', role=User.LANDLORD)
user.set_password(password)
user.save()

profile, _ = LandlordProfile.objects.get_or_create(user=user)
email_verification, _ = EmailVerification.objects.get_or_create(user=user)
code = email_verification.generate_code()
print('verify_user_id=', user.id)
print('verify_email=', email)
print('verify_code=', code)
