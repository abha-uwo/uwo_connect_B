import os
import django
import sys
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.views.super_admin_views import SuperAdminClientsListView

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.first()

print(f"Using user: {admin_user.username if admin_user else 'None'}")

factory = RequestFactory()
request = factory.get('/api/admin/clients-directory')
request.user = admin_user

view = SuperAdminClientsListView.as_view()
try:
    response = view(request)
    print(f"Status code: {response.status_code}")
    print(f"Data: {response.data}")
except Exception as e:
    import traceback
    print("CLIENTS DIRECTORY VIEW FAILED WITH EXCEPTION:")
    traceback.print_exc()
