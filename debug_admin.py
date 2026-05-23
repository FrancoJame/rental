import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')
django.setup()

from listings.models import LandlordProfile
from listings.admin import LandlordProfileAdmin
from django.contrib import admin

try:
    admin_class = LandlordProfileAdmin(LandlordProfile, admin.site)
    print('ok', admin_class)
except Exception:
    traceback.print_exc()