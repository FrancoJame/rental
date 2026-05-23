import os
import sys
from pathlib import Path
from decouple import config # 👈 Forces decouple to read your .env / Vercel variables immediately

# Ensure the project root is on the Python path for Vercel.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')

from django.core.wsgi import get_wsgi_application

# Clean up initialization order so third-party apps load environment variables correctly
app = get_wsgi_application()