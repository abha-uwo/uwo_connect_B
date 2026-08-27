import os
import sys
import django

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Contact, Message, Client, Conversation

def fast_sync():
    client = Client.objects.first()
    print("Syncing contacts for client:", client.business_name)
    
    # Get latest message per platform_id / from_address / to_address
    msgs = list(Message.objects.filter(client=client).order_by('-created_at')[:500])
    
    latest_msg_map = {}
    for m in msgs:
        for addr in [m.from_address, m.to_address]:
            if addr and addr not in latest_msg_map:
                latest_msg_map[addr] = m

    updated = 0
    for c in Contact.objects.filter(client=client):
        m = latest_msg_map.get(c.platform_id) or latest_msg_map.get(c.phone_number)
        if m:
            c.updated_at = m.created_at
            c.save()
            updated += 1
            
            # Sync conversation
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

    print(f"Fast synced {updated} active contacts & conversations with latest message timestamps!")

if __name__ == '__main__':
    fast_sync()
