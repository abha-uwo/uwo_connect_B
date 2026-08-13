import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Client

User = get_user_model()
emails_to_clear = ['devanshclg2004@gmail.com', 'devanshtantwaynir@gmail.com']

for email in emails_to_clear:
    try:
        user = User.objects.get(email=email)
        client = user.client
        client.instagram_config = None
        client.instagram_enabled = False
        client.save()
        print(f"Successfully removed Instagram credentials for {email}")
    except User.DoesNotExist:
        print(f"User {email} not found")
    except Exception as e:
        print(f"Error for {email}: {e}")
