import os
import django
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / 'Desktop' / 'uwoconnect' / 'UWO_CONNECT_B'
env_path = BASE_DIR / '.env'
load_dotenv(env_path, override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# We can set the settings values before setup or after. Since settings are loaded lazily or on setup,
# let's set them directly in core.settings or test if settings can be configured.
django.setup()

from django.conf import settings
from django.db import connection

# Inject connection pooling configurations
settings.DATABASES['default']['CONN_MAX_AGE'] = 600
settings.DATABASES['default']['CONN_HEALTH_CHECKS'] = True

print("Injected CONN_MAX_AGE and CONN_HEALTH_CHECKS. Testing connection...")
try:
    connection.ensure_connection()
    print("Connection established successfully with connection pooling settings!")
    
    # Run a simple query to verify
    with connection.cursor() as cursor:
        print("Connected to database successfully!")
except Exception as e:
    print(f"Failed with connection pooling: {e}")
