import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Client, Conversation
from django.db.models import Q

client = Client.objects.first()
channel_filter = 'WHATSAPP'
allowed_channel_contact_ids = set(Conversation.objects.filter(
    client=client, 
    channel=channel_filter.upper()
).values_list('contact_platform_id', flat=True).distinct())

print(f"Allowed: {len(allowed_channel_contact_ids)}")

has_any_convo_ids = set(Conversation.objects.filter(client=client).values_list('contact_platform_id', flat=True).distinct())
print(f"Has Any: {len(has_any_convo_ids)}")

from api.models import Contact
qs = Contact.objects.filter(client=client)
qs = qs.filter(Q(platform_id__in=allowed_channel_contact_ids) | ~Q(platform_id__in=has_any_convo_ids))
print(f"Result Count: {qs.count()}")
