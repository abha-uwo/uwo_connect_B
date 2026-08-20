import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('.')
django.setup()

from django.test import RequestFactory
from api.models import User
from api.views.super_admin_views import (
    SuperAdminTeamAnalyticsView,
    SuperAdminProjectsListView,
    SuperAdminTeamListView,
    SuperAdminOverviewView
)

admin = User.objects.filter(role='SUPER_ADMIN').first() or User.objects.first()
factory = RequestFactory()

for name, view, url in [
    ('team-analytics', SuperAdminTeamAnalyticsView.as_view(), '/api/admin/team-analytics/'),
    ('all-projects', SuperAdminProjectsListView.as_view(), '/api/admin/all-projects/'),
    ('all-team', SuperAdminTeamListView.as_view(), '/api/admin/all-team/'),
    ('overview', SuperAdminOverviewView.as_view(), '/api/admin/overview/')
]:
    req = factory.get(url)
    req.user = admin
    try:
        res = view(req)
        print(f"[{name}] -> OK {res.status_code}", flush=True)
    except Exception as e:
        print(f"[{name}] -> ERROR: {e}", flush=True)
        traceback.print_exc()
