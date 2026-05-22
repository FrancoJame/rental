import os
import sys
from pathlib import Path

# Ensure the project root is on the Python path for Vercel.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')

import django
from django.core.wsgi import get_wsgi_application

django.setup()

application = get_wsgi_application()
app = application
