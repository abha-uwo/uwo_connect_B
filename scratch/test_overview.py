import os, sys
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.views.super_admin_views import SuperAdminOverviewView
import time

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
print(f"Using user: {admin_user.username if admin_user else 'None'}", flush=True)

factory = RequestFactory()
request = factory.get('/api/admin/overview/')
request.user = admin_user

view = SuperAdminOverviewView.as_view()
t0 = time.time()
try:
    response = view(request)
    print(f"Status code: {response.status_code}, took {time.time() - t0:.2f}s", flush=True)
    print(f"Keys in response data: {list(response.data.keys())}", flush=True)
except Exception as e:
    import traceback
    print("OVERVIEW VIEW FAILED WITH EXCEPTION:", flush=True)
    traceback.print_exc()
