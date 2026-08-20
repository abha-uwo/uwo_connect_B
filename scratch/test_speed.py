import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
import django
django.setup()

from django.test import RequestFactory
from api.views.super_admin_views import SuperAdminClientDetailDashboardView
from api.models import User, Client

client = Client.objects.first()
if not client:
    print("No client found")
    sys.exit(0)

client_id = client.id
admin = User.objects.filter(is_superuser=True).first() or User.objects.first()

factory = RequestFactory()
request = factory.get(f'/api/admin/clients/{client_id}/dashboard/')
request.user = admin

view = SuperAdminClientDetailDashboardView.as_view()

t0 = time.time()
response = view(request, id=client_id)
t1 = time.time()

print(f"Status Code: {response.status_code}")
print(f"Time Taken: {t1 - t0:.3f}s")
