"""
Centralized Channel Feature Lock & Permission Validator for UWO CONNECT
"""

GLOBAL_AVAILABLE_CHANNELS = ['whatsapp', 'facebook', 'instagram']

GLOBAL_ALL_CHANNELS = [
    'whatsapp', 'facebook', 'instagram', 'gmail', 'outlook', 'onedrive',
    'google_calendar', 'google_sheets', 'google_docs', 'google_slides',
    'zoho', 'youtube', 'google_news', 'telegram', 'linkedin', 'twitter', 'tiktok'
]

GLOBAL_COMING_SOON_CHANNELS = [
    'telegram', 'linkedin', 'twitter', 'youtube', 'tiktok',
    'outlook', 'onedrive', 'google_calendar', 'google_sheets',
    'google_docs', 'google_slides', 'zoho', 'google_news'
]

def is_channel_globally_available(channel_name):
    """Check if channel is among active user-facing features."""
    if not channel_name:
        return False
    return str(channel_name).lower().strip() in GLOBAL_ALL_CHANNELS

def validate_channel_access(user, channel_name):
    """
    Validates hierarchical channel access:
    1. Admin Bypass
    2. Client-level Admin permission Check (Client.has_channel_access)
    3. Team Member assigned permission Check
    """
    if not user or not user.is_authenticated:
        return False, "Authentication required.", 401

    key = str(channel_name).lower().strip()

    # 1. Super Admin / Admin role check
    role = getattr(user, 'role', '').upper()
    enterprise_role = getattr(user, 'enterprise_role', '').upper()
    if role == 'ADMIN' or enterprise_role in ('SUPER_ADMIN', 'ORG_ADMIN'):
        return True, None, 200

    # 2. Client Access Check
    client = getattr(user, 'client', None)
    if not client:
        return False, "No active workspace/client associated with this user.", 403

    if not client.has_channel_access(key):
        return False, f"Access to {key.capitalize()} is not enabled for this workspace.", 403

    # 4. Team Member (Agent/Employee) Granular Permission Check
    if role in ('AGENT', 'EMPLOYEE') or enterprise_role not in ('SUPER_ADMIN', 'ORG_ADMIN'):
        # Managers & Admins have workspace-wide access to client's enabled channels
        if enterprise_role in ('MANAGER', 'HR'):
            return True, None, 200

        assigned_channels = getattr(user, 'assigned_social_channels', []) or []
        # If user has channels assigned, check if this channel is in assigned list
        # Match 'whatsapp', 'wa_default', 'instagram', 'ig_main', 'facebook', 'fb_page'
        matches = any(
            key in str(ch).lower() or str(ch).lower() in key
            for ch in assigned_channels
        )
        if assigned_channels and not matches:
            return False, f"You do not have permission to access {key.capitalize()}.", 403

    return True, None, 200


def get_user_allowed_channels(user, client=None):
    """
    Returns the list of uppercase channel names ('WHATSAPP', 'FACEBOOK', 'INSTAGRAM', 'GMAIL', 'TELEGRAM')
    that a given user is permitted to view/access in their workspace.
    """
    if not user or not user.is_authenticated:
        return []

    target_client = client or getattr(user, 'client', None)
    if not target_client:
        return []

    # 1. Determine all channels enabled on this client workspace
    client_available = []
    if target_client.has_channel_access('whatsapp'):
        client_available.append('WHATSAPP')
    if target_client.has_channel_access('facebook'):
        client_available.append('FACEBOOK')
    if target_client.has_channel_access('instagram'):
        client_available.append('INSTAGRAM')
    if getattr(target_client, 'gmail_enabled', False):
        client_available.append('GMAIL')
    if getattr(target_client, 'telegram_enabled', False):
        client_available.append('TELEGRAM')

    # If user is ADMIN or primary CLIENT owner or MANAGER, grant all client-available channels
    role = getattr(user, 'role', '').upper()
    enterprise_role = getattr(user, 'enterprise_role', '').upper()
    if role in ('ADMIN', 'CLIENT') or enterprise_role in ('SUPER_ADMIN', 'ORG_ADMIN', 'MANAGER', 'HR'):
        return client_available

    # 2. Team Member (Agent/Employee/Intern) Granular Channel Check
    assigned = getattr(user, 'assigned_social_channels', []) or []
    permission_matrix = getattr(user, 'permission_matrix', {}) or {}

    # If no specific channels have been assigned yet (default on invite/qr login),
    # inherit all channels available on the client
    if not assigned:
        allowed = list(client_available)
    else:
        allowed = []
        for ch in client_available:
            ch_lower = ch.lower()
            # Match standard names ('whatsapp', 'facebook', 'instagram') and legacy keys ('wa_default', 'fb_page', 'ig_main', 'gmail_main')
            matched = any(
                ch_lower in str(a).lower() or 
                str(a).lower() in ch_lower or
                (ch == 'WHATSAPP' and str(a).lower() in ['wa_default', 'wa', 'whatsapp']) or
                (ch == 'FACEBOOK' and str(a).lower() in ['fb_page', 'fb', 'facebook']) or
                (ch == 'INSTAGRAM' and str(a).lower() in ['ig_main', 'ig', 'instagram']) or
                (ch == 'GMAIL' and str(a).lower() in ['gmail_main', 'gmail']) or
                (ch == 'TELEGRAM' and str(a).lower() in ['tg_main', 'telegram'])
                for a in assigned
            )
            if matched:
                allowed.append(ch)

    # 3. Check permission_matrix: if a feature is explicitly marked 'NONE', remove it
    filtered_allowed = []
    for ch in allowed:
        matrix_key = ch.lower()
        if permission_matrix.get(matrix_key) == 'NONE':
            continue
        filtered_allowed.append(ch)

    return filtered_allowed


def log_channel_permission_change(admin_user_identifier, client, channel, action, previous_state, new_state, notes=""):
    """
    Helper to record channel permission modifications in ChannelAuditLog.
    """
    try:
        from api.models import ChannelAuditLog
        ChannelAuditLog.objects.create(
            admin_user=str(admin_user_identifier),
            client=client,
            channel=str(channel).lower().strip(),
            action=action,
            previous_state=previous_state if isinstance(previous_state, dict) else {'state': previous_state},
            new_state=new_state if isinstance(new_state, dict) else {'state': new_state},
            notes=notes
        )
    except Exception as e:
        print(f"[ChannelAuditLog] Failed to log permission change: {e}")

