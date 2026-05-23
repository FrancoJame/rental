import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass1234')
    print('created superuser', admin)

client = Client()
client.force_login(admin)
resp = client.get('/admin/listings/emailverification/')
print('status', resp.status_code)
print(resp.content.decode('utf-8')[:8000])
