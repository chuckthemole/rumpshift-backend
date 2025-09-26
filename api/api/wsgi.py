import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent      # api/api/
PROJECT_ROOT = BASE_DIR.parent                  # api/
REPO_ROOT = PROJECT_ROOT.parent                 # rumpshift-backend

# Add project root for Django project
sys.path.insert(0, str(PROJECT_ROOT))
# Add repo root so `shared` is importable
sys.path.insert(0, str(REPO_ROOT))

# Load .env from api/ (where manage.py lives)
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

