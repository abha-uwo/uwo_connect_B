import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Conversation, Contact, Client
client = Client.objects.first()
null_convos = Conversation.objects.filter(client=client, contact_platform_id__isnull=True).count()
empty_convos = Conversation.objects.filter(client=client, contact_platform_id='').count()
null_contacts = Contact.objects.filter(client=client, platform_id__isnull=True).count()
empty_contacts = Contact.objects.filter(client=client, platform_id='').count()
print(f"Null convos: {null_convos}, Empty convos: {empty_convos}")
print(f"Null contacts: {null_contacts}, Empty contacts: {empty_contacts}")
