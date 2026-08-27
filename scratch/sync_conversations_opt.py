import os
import sys
import django

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Q
from api.models import Contact, Message, Conversation

def sync():
    print("Starting Optimized Conversation Synchronization...")
    contacts = Contact.objects.all()
    print(f"Total contacts to process: {contacts.count()}")
    
    created_count = 0
    updated_count = 0
    
    for contact in contacts:
        client = contact.client
        pid = contact.platform_id
        if not pid:
            continue
            
        # Get the latest message for this contact
        latest_msg = Message.objects.filter(
            Q(client=client),
            Q(from_address=pid) | Q(to_address=pid)
        ).order_by('-created_at').first()
        
        if not latest_msg:
            continue
            
        channel = latest_msg.channel or 'WHATSAPP'
        
        convo, created = Conversation.objects.get_or_create(
            client=client,
            contact_platform_id=pid,
            channel=channel,
            defaults={
                'contact': contact,
                'last_message_summary': latest_msg.body,
                'last_message_at': latest_msg.created_at
            }
        )
        
        if created:
            created_count += 1
        else:
            convo.last_message_summary = latest_msg.body
            convo.last_message_at = latest_msg.created_at
            if not convo.contact:
                convo.contact = contact
            convo.save()
            updated_count += 1
            
    print(f"Sync complete. Created {created_count} new conversations. Updated {updated_count} conversations.")
    print(f"Total Conversations in database: {Conversation.objects.count()}")

if __name__ == '__main__':
    sync()
