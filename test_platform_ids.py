import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Contact
for c in Contact.objects.all()[:15]:
    name_str = (c.name or '').encode('ascii', 'ignore').decode()
    print(f"Name: {name_str}, Platform ID: {c.platform_id}, Phone: {c.phone_number}")
