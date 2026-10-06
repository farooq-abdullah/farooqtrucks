import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Serverless hosts import this entry point from the repository root; local
# manage.py and Gunicorn normally start with backend already on the import path.
backend_directory = str(Path(__file__).resolve().parent.parent)
if backend_directory not in sys.path:
    sys.path.insert(0, backend_directory)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
