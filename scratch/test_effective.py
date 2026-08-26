import os, sys
sys.path.insert(0, r'c:\Users\USER\Desktop\Connect\uwoconnectforRB')
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import User, Client, GlobalConnector
from api.utils.channel_permissions import get_user_effective_connectors

print("--- GLOBAL CONNECTORS IN DB ---")
for gc in GlobalConnector.objects.all():
    print(f"Key: {gc.connector_key}, is_active: {gc.is_active}")

client_user = User.objects.filter(role='CLIENT').first()
if client_user:
    client = getattr(client_user, 'client', None) or Client.objects.first()
    print(f"\n--- CLIENT USER: {client_user.username}, Client: {client} ---")
    eff = get_user_effective_connectors(client_user, client=client)
    for k, v in eff.items():
        print(f"{k}: global_active={v.get('global_active')}, client_enabled={v.get('client_enabled')}, effective_access={v.get('effective_access')}")
else:
    print("No client user found")
