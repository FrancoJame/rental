import os
import sys
from pathlib import Path

# Ensure project root is on the path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_project.settings')

import django
django.setup()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
