import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Contact, Client
from django.db.models import Q
client = Client.objects.first()
qs = Contact.objects.filter(client=client)
try:
    qs = qs.filter(~Q(platform_id__in=set()))
    print("Count works:", qs.count())
except Exception as e:
    print("Error:", e)
