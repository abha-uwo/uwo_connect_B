import urllib.request
import json
import time
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
import django
django.setup()

from api.models import User
from rest_framework_simplejwt.tokens import RefreshToken

admin = User.objects.filter(role='SUPER_ADMIN').first() or User.objects.filter(is_superuser=True).first() or User.objects.first()
token = str(RefreshToken.for_user(admin).access_token)

endpoints = [
    '/api/admin/team-analytics/',
    '/api/admin/all-projects/',
    '/api/admin/all-team/',
    '/api/admin/overview/',
    '/api/clients/'
]

print(f"Testing as Super Admin: {admin.username} ({admin.email})", flush=True)
for ep in endpoints:
    url = f"http://127.0.0.1:8080{ep}"
    t0 = time.time()
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = time.time() - t0
            data = resp.read()
            print(f"[SUCCESS] {ep} -> HTTP {resp.status} in {elapsed:.3f}s ({len(data)} bytes)", flush=True)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[ERROR] {ep} -> FAILED in {elapsed:.3f}s: {e}", flush=True)
