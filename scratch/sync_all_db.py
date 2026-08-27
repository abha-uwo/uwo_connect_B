import os
import sys
import django

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Contact, Message, Client, Conversation
from django.db.models import Q

def sync_all():
    for client in Client.objects.all():
        contacts = Contact.objects.filter(client=client)
        print(f"Processing {contacts.count()} contacts for client {client.business_name}...")
        for c in contacts:
            msg = Message.objects.filter(client=client).filter(
                Q(from_address=c.platform_id) | Q(to_address=c.platform_id)
            ).order_by('-created_at').first()
            
            if msg and msg.created_at:
                # Update contact updated_at to match latest message created_at
                Contact.objects.filter(id=c.id).update(updated_at=msg.created_at)
                
                # Update conversation
                convo = Conversation.objects.filter(client=client, contact_platform_id=c.platform_id).first()
                if not convo:
                    Conversation.objects.create(
                        client=client,
                        contact_platform_id=c.platform_id,
                        contact=c,
                        channel=msg.channel or 'WHATSAPP',
                        last_message_summary=msg.body,
                        last_message_at=msg.created_at
                    )
                else:
                    convo.last_message_summary = msg.body
                    convo.last_message_at = msg.created_at
                    convo.contact = c
                    convo.save()

    print("Complete DB sync finished successfully!")

if __name__ == '__main__':
    sync_all()
