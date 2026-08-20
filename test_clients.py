import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Client, Conversation
for client in Client.objects.all():
    print(f"Client ID: {client.id}, Name: {client.name}")
    print(f"  Contacts: {client.contacts.count()}")
    print(f"  WA Conv: {Conversation.objects.filter(client=client, channel='WHATSAPP').count()}")
    print(f"  IG Conv: {Conversation.objects.filter(client=client, channel='INSTAGRAM').count()}")
