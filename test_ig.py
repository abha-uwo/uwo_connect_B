import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Conversation, Client
client = Client.objects.first()
ig_count = Conversation.objects.filter(client=client, channel='INSTAGRAM').count()
wa_count = Conversation.objects.filter(client=client, channel='WHATSAPP').count()
print(f"IG: {ig_count}, WA: {wa_count}")
