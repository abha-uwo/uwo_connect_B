import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import ActiveCallSession

count, _ = ActiveCallSession.objects.all().delete()
print(f"Deleted {count} stuck call sessions.")
