import os
import sys
import django

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Contact, Message, Client, Conversation
from django.db.models import Q

def sync_contacts():
    count = 0
    for client in Client.objects.all():
        for c in Contact.objects.filter(client=client):
            last_m = Message.objects.filter(client=client).filter(
                Q(from_address=c.platform_id) | Q(to_address=c.platform_id)
            ).order_by('-created_at').first()
            if last_m and last_m.created_at:
                c.updated_at = last_m.created_at
                c.save()
                
                # Also ensure Conversation has last_message_summary and last_message_at
                convo = Conversation.objects.filter(
                    client=client,
                    contact_platform_id=c.platform_id
                ).first()
                if not convo:
                    convo = Conversation.objects.create(
                        client=client,
                        contact_platform_id=c.platform_id,
                        contact=c,
                        channel=last_m.channel or 'WHATSAPP',
                        last_message_summary=last_m.body,
                        last_message_at=last_m.created_at
                    )
                else:
                    convo.last_message_summary = last_m.body
                    convo.last_message_at = last_m.created_at
                    convo.contact = c
                    convo.save()
                count += 1
    print(f"Synced {count} contacts & conversations with latest message timestamps.")

if __name__ == '__main__':
    sync_contacts()
