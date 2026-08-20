import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Conversation, Client
client = Client.objects.first()
print(f"Total Conv: {Conversation.objects.filter(client=client).count()}")
