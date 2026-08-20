import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Message
import pprint

msgs = Message.objects.order_by('-created_at')[:2]
for msg in msgs:
    print(f"ID: {msg.id}")
    print(f"Status: {msg.status}")
    print(f"Body: {msg.body}")
    print("Metadata:")
    pprint.pprint(msg.metadata)
    print("-" * 50)
