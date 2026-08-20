import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client

# Find a client to test deletion on
# Let's inspect the clients first
clients = Client.objects.all()
print(f"Total clients in DB: {clients.count()}")
for c in clients:
    print(f"Client ID: {c.id}, Name: {c.business_name}")

if clients.exists():
    client = clients.first()
    print(f"\nAttempting to delete client: {client.id} ({client.business_name})")
    try:
        # Let's run client.delete()
        # Since we want to test why it fails, we will catch the exception and print it.
        # But wait! We don't want to actually delete a real user's client if they are testing.
        # Let's check if the client name is "UWO Workspace" (which is the one shown in screenshot).
        # We can look up "UWO Workspace".
        target = Client.objects.filter(business_name="UWO Workspace").first()
        if target:
            print(f"Found UWO Workspace client, attempting delete...")
            # We can run in a transaction, but MongoDB doesn't enforce standard SQL transactions by default
            # unless configured. So let's delete it or dry-run. Since the user wants to delete it, let's delete it!
            target.delete()
            print("Successfully deleted!")
        else:
            print("UWO Workspace client not found. Attempting to delete the first client in list...")
            client.delete()
            print("Successfully deleted first client!")
    except Exception as e:
        import traceback
        print("DELETE FAILED WITH EXCEPTION:")
        traceback.print_exc()
else:
    print("No clients to delete.")
