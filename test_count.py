import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Contact, Client
client = Client.objects.first()
print(f"Total contacts: {Contact.objects.filter(client=client).count()}")
