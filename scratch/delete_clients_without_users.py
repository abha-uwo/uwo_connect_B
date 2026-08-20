import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client

clients = Client.objects.all()
print(f"Total clients before cleanup: {clients.count()}")

deleted_count = 0
for client in list(clients):
    user_count = client.users.count()
    print(f"Client: {client.id} | Name: {client.business_name} | Users: {user_count}")
    if user_count == 0:
        print(f"-> No users found! Deleting client {client.business_name}...")
        client.delete()
        deleted_count += 1

print(f"\nCleanup complete. Deleted {deleted_count} clients.")
print(f"Total clients remaining: {Client.objects.count()}")
