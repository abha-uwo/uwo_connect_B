import os
import sys
import django

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from api.models import Client, Contact, Message, Conversation

def sync():
    print("Starting Conversation Synchronization...")
    messages = Message.objects.all().order_by('created_at')
    print(f"Total messages to process: {messages.count()}")
    
    created_count = 0
    updated_count = 0
    
    for msg in messages:
        client = msg.client
        if not client:
            continue
            
        platform_id = msg.from_address if msg.message_type == 'INCOMING' else msg.to_address
        if not platform_id:
            continue
            
        channel = msg.channel or 'WHATSAPP'
        
        # Get associated Contact
        contact = Contact.objects.filter(client=client, platform_id=platform_id).first()
        
        convo, created = Conversation.objects.get_or_create(
            client=client,
            contact_platform_id=platform_id,
            channel=channel,
            defaults={
                'contact': contact,
                'last_message_summary': msg.body,
                'last_message_at': msg.created_at
            }
        )
        
        if created:
            created_count += 1
        else:
            convo.last_message_summary = msg.body
            convo.last_message_at = msg.created_at
            if not convo.contact and contact:
                convo.contact = contact
            convo.save()
            updated_count += 1
            
    print(f"Sync complete. Created {created_count} new conversations. Updated {updated_count} conversations.")
    print(f"Total Conversations in database: {Conversation.objects.count()}")

if __name__ == '__main__':
    sync()
