"""Exercise the built frontend through production Django/WhiteNoise without Docker."""
import os
from pathlib import Path
import re
import secrets
import sys
import threading
from wsgiref.simple_server import make_server
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.update(DJANGO_SETTINGS_MODULE='config.settings', DJANGO_DEBUG='false',
                  DJANGO_SECRET_KEY=secrets.token_urlsafe(48), DJANGO_ALLOWED_HOSTS='127.0.0.1')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
with make_server('127.0.0.1', 8001, application) as server:
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        base = 'http://127.0.0.1:8001'
        response = requests.get(base, timeout=10)
        assert response.status_code == 200 and 'farooqtrucks' in response.text
        for page in ('/plan', '/route', '/logs'):
            direct = requests.get(base + page, timeout=10)
            assert direct.status_code == 200 and direct.text == response.text, page
        assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', response.text)
        assert assets
        for asset in assets:
            result = requests.get(base + asset, timeout=10)
            assert result.status_code == 200 and len(result.content) > 0, asset
        assert requests.get(base + '/api/health/', timeout=10).json()['database_required'] is False
        assert requests.get(base + '/assets/figma/934c0.svg', timeout=10).status_code == 200
        assert requests.get(base + '/assets/inspection.svg', timeout=10).status_code == 200
        print('Production smoke passed: HTML, built JS/CSS, identity, waypoint and API health.')
    finally:
        server.shutdown(); thread.join()
