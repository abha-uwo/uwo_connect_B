import os
import sys
import django

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Contact, Message, Client, Conversation

def fast_db_sync():
    for client in Client.objects.all():
        print(f"Fast syncing {client.business_name}...")
        # Get all unique platform_ids for messages
        all_msgs = Message.objects.filter(client=client).order_by('-created_at')
        
        seen_addresses = {}
        for m in all_msgs:
            if m.from_address and m.from_address not in seen_addresses:
                seen_addresses[m.from_address] = m
            if m.to_address and m.to_address not in seen_addresses:
                seen_addresses[m.to_address] = m

        for c in Contact.objects.filter(client=client):
            m = seen_addresses.get(c.platform_id) or seen_addresses.get(c.phone_number)
            if m and m.created_at:
                Contact.objects.filter(id=c.id).update(updated_at=m.created_at)
                
                convo = Conversation.objects.filter(client=client, contact_platform_id=c.platform_id).first()
                if not convo:
                    Conversation.objects.create(
                        client=client,
                        contact_platform_id=c.platform_id,
                        contact=c,
                        channel=m.channel or 'WHATSAPP',
                        last_message_summary=m.body,
                        last_message_at=m.created_at
                    )
                else:
                    convo.last_message_summary = m.body
                    convo.last_message_at = m.created_at
                    convo.save()

    print("Fast DB sync completed!")

if __name__ == '__main__':
    fast_db_sync()
