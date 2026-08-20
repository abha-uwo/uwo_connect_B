import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client

print("Running client_comparison query...")
clients = list(Client.objects.all())
print(f"Loaded {len(clients)} clients.")

for c in clients:
    print(f"\nProcessing client: {c.business_name}")
    c_primary = c.users.filter(role='CLIENT').first() or c.users.first()
    print(f"c_primary: {c_primary}")
    
    if c_primary and c_primary.last_active_at:
        last_active_dt = c_primary.last_active_at
    else:
        last_active_dt = c.updated_at
        
    last_active_val = last_active_dt.isoformat() if last_active_dt else None
    print(f"last_active: {last_active_val}")

print("\nAll queries ran successfully!")
