import os, sys, django, time
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.views.super_admin_views import SuperAdminClientsListView

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

factory = RequestFactory()
request = factory.get('/api/admin/clients-directory/')
request.user = admin_user

view = SuperAdminClientsListView.as_view()
t0 = time.time()
response = view(request)
print(f"SuperAdminClientsListView status: {response.status_code}, took: {time.time() - t0:.3f}s", flush=True)
