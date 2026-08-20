import os
import sys
import time
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
import django
django.setup()

from django.test import RequestFactory
from api.models import User
from api.views.super_admin_views import (
    SuperAdminProjectsListView,
    SuperAdminTeamListView,
    SuperAdminTeamAnalyticsView,
    SuperAdminOverviewView
)
from api.views.client_views import ClientViewSet

admin = User.objects.filter(is_superuser=True).first() or User.objects.first()
factory = RequestFactory()

endpoints = [
    ("team-analytics", SuperAdminTeamAnalyticsView.as_view(), "/api/admin/team-analytics/"),
    ("all-projects", SuperAdminProjectsListView.as_view(), "/api/admin/all-projects/"),
    ("all-team", SuperAdminTeamListView.as_view(), "/api/admin/all-team/"),
    ("overview", SuperAdminOverviewView.as_view(), "/api/admin/overview/"),
    ("clients", ClientViewSet.as_view({'get': 'list'}), "/api/clients/"),
]

for name, view, url in endpoints:
    t0 = time.time()
    request = factory.get(url)
    request.user = admin
    try:
        response = view(request)
        elapsed = time.time() - t0
        print(f"[{name}] Status: {response.status_code} in {elapsed:.2f}s", flush=True)
        if response.status_code != 200:
            print(f"Response data: {response.data}", flush=True)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[{name}] FAILED in {elapsed:.2f}s with exception:", flush=True)
        traceback.print_exc()
