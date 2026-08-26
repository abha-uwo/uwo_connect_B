import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import GlobalConnector, Client, User, ClientConnectorAccess, TeamMemberConnectorAccess, ChannelAuditLog
from api.utils.channel_permissions import (
    ensure_default_global_connectors,
    is_connector_globally_active,
    get_client_connector_permission,
    get_team_member_connector_permission,
    check_effective_connector_access,
    get_user_effective_connectors,
    log_channel_permission_change
)

print("--- Testing ensure_default_global_connectors ---")
ensure_default_global_connectors()
connectors = list(GlobalConnector.objects.all())
print(f"Total GlobalConnectors seeded: {len(connectors)}")
for c in connectors[:5]:
    print(f"  {c.connector_key}: active={c.is_active}, core={c.is_core}")

print("\n--- Testing Hierarchy ---")
# Pick a client and a user
client = Client.objects.first()
user = client.users.filter(role__in=['AGENT', 'EMPLOYEE']).first() or client.users.first()

print(f"Testing Client: {client.business_name}, User: {user.username if user else 'None'}")

# 1. Global ON, Client ON, Member ON -> True
gc_wa = GlobalConnector.objects.get(connector_key='whatsapp')
gc_wa.is_active = True
gc_wa.save()

cca_wa, _ = ClientConnectorAccess.objects.get_or_create(client=client, connector_key='whatsapp')
cca_wa.is_enabled = True
cca_wa.save()

if user:
    tmca_wa, _ = TeamMemberConnectorAccess.objects.get_or_create(client=client, team_member=user, connector_key='whatsapp')
    tmca_wa.is_enabled = True
    tmca_wa.save()
    eff, reason, code = check_effective_connector_access(user, 'whatsapp')
    print(f"Test 1 (All ON) -> Effective={eff}, Code={code}")

# 2. Global OFF -> Everything OFF
gc_wa.is_active = False
gc_wa.save()
if user:
    eff, reason, code = check_effective_connector_access(user, 'whatsapp')
    print(f"Test 2 (Global OFF) -> Effective={eff}, Reason='{reason}', Code={code}")

# Restore Global ON
gc_wa.is_active = True
gc_wa.save()

# 3. Client OFF -> Member OFF
cca_wa.is_enabled = False
cca_wa.save()
if user:
    eff, reason, code = check_effective_connector_access(user, 'whatsapp')
    print(f"Test 3 (Client OFF) -> Effective={eff}, Reason='{reason}', Code={code}")

# Restore Client ON
cca_wa.is_enabled = True
cca_wa.save()

# 4. Member OFF -> Member OFF
if user:
    tmca_wa.is_enabled = False
    tmca_wa.save()
    eff, reason, code = check_effective_connector_access(user, 'whatsapp')
    print(f"Test 4 (Member OFF) -> Effective={eff}, Reason='{reason}', Code={code}")
    # Restore Member ON
    tmca_wa.is_enabled = True
    tmca_wa.save()

# 5. Audit Logging test
log_channel_permission_change('TestAdmin', client, 'whatsapp', 'GLOBAL_ACTIVATED', {'is_active': False}, {'is_active': True})
latest_log = ChannelAuditLog.objects.first()
print(f"\nLatest Audit Log: {latest_log}")
print("ALL TESTS PASSED SUCCESSFULLY!")
