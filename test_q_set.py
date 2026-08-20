import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Contact, Client
from django.db.models import Q
client = Client.objects.first()
qs = Contact.objects.filter(client=client)
my_set = set(['123', '456'])
try:
    qs = qs.filter(Q(platform_id__in=my_set) | ~Q(platform_id__in=set()))
    print("Set in Q works:", len(list(qs)))
except Exception as e:
    print("Error:", e)
