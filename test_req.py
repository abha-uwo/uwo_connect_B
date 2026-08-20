import os, django, urllib.request, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import User
user = User.objects.filter(role='CLIENT').first()
token = str(RefreshToken.for_user(user).access_token)
req = urllib.request.Request('http://localhost:8080/api/contacts/?limit=10&offset=0&preferred_channel=WHATSAPP')
req.add_header('Authorization', f'Bearer {token}')
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"Success! Contacts returned: {len(data['results']) if 'results' in data else len(data)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
