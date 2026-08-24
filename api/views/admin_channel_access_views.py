import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from api.models import Client, User, ChannelAuditLog
from api.utils.channel_permissions import (
    GLOBAL_AVAILABLE_CHANNELS,
    GLOBAL_COMING_SOON_CHANNELS,
    log_channel_permission_change
)

from ..repositories.client_repository import ClientRepository

def check_admin_privileges(user):
    if not user or not user.is_authenticated:
        return False
    role = getattr(user, 'role', '').upper()
    enterprise_role = getattr(user, 'enterprise_role', '').upper()
    return (
        role == 'ADMIN' or
        enterprise_role in ('SUPER_ADMIN', 'ORG_ADMIN', 'ADMIN') or
        getattr(user, 'is_staff', False) or
        getattr(user, 'is_superuser', False)
    )

def get_client_by_id(client_id):
    try:
        c = ClientRepository.get_client(id=client_id)
        if c:
            return c
    except Exception:
        pass
    try:
        return Client.objects.filter(id=client_id).first()
    except Exception:
        return None

class AdminChannelAccessMatrixView(APIView):
    """
    Returns global channel matrix for all clients, including:
    - Admin-granted access status
    - Live connection status
    - Team member assignment summary
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not check_admin_privileges(request.user):
            return Response({"error": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        clients = Client.objects.all().order_by('-created_at')
        search = request.query_params.get('search', '').strip().lower()

        results = []
        for client in clients:
            if search:
                matches = (
                    search in (client.business_name or '').lower() or
                    search in str(client.id) or
                    search in (client.phone_number or '').lower()
                )
                if not matches:
                    continue

            # Connection calculations
            is_wa_connected = bool(
                client.whatsapp_access_token and client.whatsapp_phone_number_id or
                client.whatsapp_waba_id
            )
            is_fb_connected = bool(
                client.facebook_enabled or 
                (client.facebook_config and client.facebook_config.get('page_id'))
            )
            is_ig_connected = bool(
                client.instagram_enabled or
                (client.instagram_config and (client.instagram_config.get('instagram_business_id') or client.instagram_config.get('username')))
            )

            # Permissions
            perms = client.get_channel_access_dict()

            # Team member count
            team_count = client.users.count()

            # Latest audit log
            latest_log = client.channel_audit_logs.first()
            last_audit_data = None
            if latest_log:
                last_audit_data = {
                    'admin': latest_log.admin_user,
                    'action': latest_log.action,
                    'channel': latest_log.channel,
                    'timestamp': latest_log.timestamp.isoformat()
                }

            results.append({
                'client_id': str(client.id),
                'business_name': client.business_name,
                'phone_number': client.phone_number,
                'plan': client.plan,
                'status': client.status,
                'team_members_count': team_count,
                'channel_access': perms,
                'channel_connections': {
                    'whatsapp': {
                        'connected': is_wa_connected,
                        'waba_id': client.whatsapp_waba_id or None,
                        'phone_id': client.whatsapp_phone_number_id or None
                    },
                    'facebook': {
                        'connected': is_fb_connected,
                        'page_name': (client.facebook_config or {}).get('page_name') or None
                    },
                    'instagram': {
                        'connected': is_ig_connected,
                        'username': (client.instagram_config or {}).get('username') or None
                    }
                },
                'last_audit': last_audit_data
            })

        return Response({
            'global_available_channels': GLOBAL_AVAILABLE_CHANNELS,
            'global_coming_soon_channels': GLOBAL_COMING_SOON_CHANNELS,
            'total_clients': len(results),
            'clients': results
        })


class AdminClientChannelAccessDetailView(APIView):
    """
    Get or modify channel access for a single client.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        if not check_admin_privileges(request.user):
            return Response({"error": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        client = get_client_by_id(client_id)
        if not client:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        perms = client.get_channel_access_dict()

        is_wa_connected = bool(client.whatsapp_access_token and client.whatsapp_phone_number_id or client.whatsapp_waba_id)
        is_fb_connected = bool(client.facebook_enabled or (client.facebook_config and client.facebook_config.get('page_id')))
        is_ig_connected = bool(client.instagram_enabled or (client.instagram_config and (client.instagram_config.get('instagram_business_id') or client.instagram_config.get('username'))))

        audit_logs = [
            {
                'id': log.id,
                'admin_user': log.admin_user,
                'channel': log.channel,
                'action': log.action,
                'previous_state': log.previous_state,
                'new_state': log.new_state,
                'notes': log.notes,
                'timestamp': log.timestamp.isoformat()
            }
            for log in client.channel_audit_logs.all()[:20]
        ]

        return Response({
            'client_id': str(client.id),
            'business_name': client.business_name,
            'channel_access': perms,
            'channel_connections': {
                'whatsapp': is_wa_connected,
                'facebook': is_fb_connected,
                'instagram': is_ig_connected
            },
            'global_available_channels': GLOBAL_AVAILABLE_CHANNELS,
            'global_coming_soon_channels': GLOBAL_COMING_SOON_CHANNELS,
            'audit_history': audit_logs
        })

    def patch(self, request, client_id):
        if not check_admin_privileges(request.user):
            return Response({"error": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        client = get_client_by_id(client_id)
        if not client:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        channel = str(request.data.get('channel', '')).lower().strip()
        enabled = request.data.get('enabled')
        notes = request.data.get('notes', '')

        from api.utils.channel_permissions import GLOBAL_ALL_CHANNELS
        if channel not in GLOBAL_ALL_CHANNELS:
            return Response({
                "error": f"Cannot modify channel '{channel}'. Unknown channel."
            }, status=status.HTTP_400_BAD_REQUEST)

        if enabled is None:
            return Response({"error": "'enabled' boolean field is required."}, status=status.HTTP_400_BAD_REQUEST)

        enabled = bool(enabled)
        previous_perms = client.get_channel_access_dict()
        previous_state = previous_perms.get(channel, False)

        # Update JSON field channel_access
        ca = client.channel_access if isinstance(client.channel_access, dict) else {}
        ca[channel] = enabled
        client.channel_access = ca

        flag_name = f"{channel}_enabled"
        if hasattr(client, flag_name):
            setattr(client, flag_name, enabled)

        client.save()

        # Audit Log Entry
        admin_name = user.username or user.email or 'Admin'
        action_type = 'ACCESS_GRANTED' if enabled else 'ACCESS_REVOKED'
        log_channel_permission_change(
            admin_user_identifier=admin_name,
            client=client,
            channel=channel,
            action=action_type,
            previous_state={'enabled': previous_state},
            new_state={'enabled': enabled},
            notes=notes or f"{action_type.replace('_', ' ').title()} by {admin_name}"
        )

        return Response({
            'success': True,
            'message': f"Channel '{channel.capitalize()}' access {'enabled' if enabled else 'disabled'} for {client.business_name}.",
            'channel': channel,
            'enabled': enabled,
            'channel_access': client.get_channel_access_dict()
        })


class AdminBulkChannelAccessView(APIView):
    """
    Bulk Grant or Revoke Channel Access for multiple clients.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        role = getattr(user, 'role', '').upper()
        enterprise_role = getattr(user, 'enterprise_role', '').upper()
        if role != 'ADMIN' and enterprise_role not in ('SUPER_ADMIN', 'ORG_ADMIN'):
            return Response({"error": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        client_ids = request.data.get('client_ids', [])
        channel = str(request.data.get('channel', '')).lower().strip()
        action = str(request.data.get('action', '')).upper().strip() # 'GRANT' or 'REVOKE'
        notes = request.data.get('notes', '')

        if not client_ids or not isinstance(client_ids, list):
            return Response({"error": "List of 'client_ids' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from api.utils.channel_permissions import GLOBAL_ALL_CHANNELS
        if channel not in GLOBAL_ALL_CHANNELS:
            return Response({
                "error": f"Invalid channel '{channel}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        if action not in ('GRANT', 'REVOKE'):
            return Response({"error": "'action' must be 'GRANT' or 'REVOKE'."}, status=status.HTTP_400_BAD_REQUEST)

        enabled = (action == 'GRANT')
        admin_name = user.username or user.email or 'Admin'
        updated_clients = []

        clients = Client.objects.filter(id__in=client_ids)
        for client in clients:
            prev_perms = client.get_channel_access_dict()
            prev_val = prev_perms.get(channel, False)

            ca = client.channel_access if isinstance(client.channel_access, dict) else {}
            ca[channel] = enabled
            client.channel_access = ca
            flag_name = f"{channel}_enabled"
            if hasattr(client, flag_name):
                setattr(client, flag_name, enabled)
            client.save()

            log_channel_permission_change(
                admin_user_identifier=admin_name,
                client=client,
                channel=channel,
                action='BULK_GRANTED' if enabled else 'BULK_REVOKED',
                previous_state={'enabled': prev_val},
                new_state={'enabled': enabled},
                notes=notes or f"Bulk {action} by {admin_name}"
            )
            updated_clients.append({
                'id': client.id,
                'business_name': client.business_name,
                'channel_access': client.get_channel_access_dict()
            })

        return Response({
            'success': True,
            'message': f"Bulk {action.lower()} completed for {len(updated_clients)} client(s) on channel '{channel.capitalize()}'.",
            'channel': channel,
            'action': action,
            'updated_count': len(updated_clients),
            'updated_clients': updated_clients
        })


class AdminChannelAuditLogView(APIView):
    """
    Query chronological channel permission changes.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not check_admin_privileges(request.user):
            return Response({"error": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        logs = ChannelAuditLog.objects.all().select_related('client').order_by('-timestamp')

        client_id = request.query_params.get('client_id')
        if client_id:
            try:
                c = get_client_by_id(client_id)
                if c:
                    logs = logs.filter(client_id=c.id)
                else:
                    logs = logs.filter(client_id=client_id)
            except Exception:
                logs = logs.filter(client_id=client_id)

        channel = request.query_params.get('channel')
        if channel:
            logs = logs.filter(channel=channel.lower().strip())

        action = request.query_params.get('action')
        if action:
            logs = logs.filter(action=action.upper().strip())

        search = request.query_params.get('search', '').strip().lower()
        if search:
            logs = [
                l for l in logs
                if search in l.admin_user.lower() or
                   search in (l.client.business_name or '').lower() or
                   search in l.channel.lower() or
                   search in l.action.lower()
            ]

        results = [
            {
                'id': log.id,
                'admin_user': log.admin_user,
                'client_id': log.client_id,
                'client_name': log.client.business_name if log.client else 'Unknown',
                'channel': log.channel,
                'action': log.action,
                'previous_state': log.previous_state,
                'new_state': log.new_state,
                'notes': log.notes,
                'timestamp': log.timestamp.isoformat()
            }
            for log in logs[:100]
        ]

        return Response({
            'total': len(results),
            'logs': results
        })
