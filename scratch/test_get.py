import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client

clients = Client.objects.all()
if clients.exists():
    first_client = clients.first()
    str_id = str(first_client.id)
    print(f"Loaded client: {first_client.business_name} with ID (type={type(first_client.id)}): {first_client.id}")
    print(f"Attempting to query with string ID: '{str_id}'")
    try:
        c1 = Client.objects.get(id=str_id)
        print(f"Success! Found: {c1.business_name}")
    except Exception as e:
        import traceback
        print("QUERY WITH STRING ID FAILED:")
        traceback.print_exc()
        
    print("\nAttempting to query with ObjectId:")
    try:
        from bson import ObjectId
        c2 = Client.objects.get(id=ObjectId(str_id))
        print(f"Success with ObjectId! Found: {c2.business_name}")
    except Exception as e:
        import traceback
        print("QUERY WITH OBJECTID FAILED:")
        traceback.print_exc()
else:
    print("No clients to test.")
