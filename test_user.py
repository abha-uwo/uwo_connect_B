import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.filter(first_name__icontains='Abha').first()
if u:
    print(f"User ID: {u.id}, Email: {u.email}, Client: {u.client.id if u.client else 'None'}")
    from api.models import Conversation
    if u.client:
        print("Conv counts for client:")
        for c in ['WHATSAPP', 'INSTAGRAM', 'FACEBOOK']:
            print(c, Conversation.objects.filter(client=u.client, channel=c).count())
else:
    print("User not found")
