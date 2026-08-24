from ..services.admin_service import AdminService
from ..repositories.system_repository import SystemRepository
from ..repositories.contact_repository import ContactRepository
from ..repositories.client_repository import ClientRepository
from ..repositories.message_repository import MessageRepository
from ..permissions.custom_permissions import IsApprovedUser
from rest_framework import status, views, viewsets, filters
from rest_framework.response import Response
from firebase_admin import auth as firebase_auth
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.views import APIView
import os
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..serializers import RegisterSerializer, UserSerializer, ClientSerializer, AutomationSerializer, WorkflowSerializer, ContactSerializer, TemplateSerializer, CampaignSerializer, SupportMessageSerializer, AuditLogSerializer, TeamInviteSerializer, ProductSerializer, OrderSerializer
from ..models import User, Client, Automation, Message, Workflow, KnowledgeDocument, KnowledgeChunk, Contact, Template, Campaign, SupportMessage, AuditLog, TeamInvite, Product, Order
import requests
import logging
logger = logging.getLogger(__name__)
from ..services.ai_service import get_ai_response, get_platform_assistance, get_rag_response, get_embedding, chunk_text, find_relevant_chunks, get_ai_draft
from ..utils.channel_permissions import get_user_allowed_channels
from rest_framework.permissions import BasePermission
from .webhook_views import WhatsAppWebhookView, FacebookInstagramWebhookView
import logging

logger = logging.getLogger(__name__)
def get_tenant_client(request):
    if not request.user or not request.user.is_authenticated:
        return None
    if request.user.role == 'ADMIN':
        client_id = request.query_params.get('client_id') or request.data.get('client_id')
        if client_id:
            try:
                return ClientRepository.get_client(id=client_id)
            except (Client.DoesNotExist, ValueError):
                pass
        return None
    return request.user.client

class ClientViewSet(viewsets.ModelViewSet):
    queryset = ClientRepository.get_all_clients()
    serializer_class = ClientSerializer
    permission_classes = [IsApprovedUser]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return ClientRepository.get_all_clients()
        return ClientRepository.filter_clients(id=self.request.user.client_id)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def suspend(self, request, pk=None):
        from ..services.client_service import ClientService
        result = ClientService.suspend_client(request, self.get_object())
        return Response(result)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reactivate(self, request, pk=None):
        from ..services.client_service import ClientService
        result = ClientService.reactivate_client(request, self.get_object())
        return Response(result)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def disconnect_meta(self, request, pk=None):
        from ..services.client_service import ClientService
        result = ClientService.disconnect_meta(request, self.get_object())
        return Response(result)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reset_ai(self, request, pk=None):
        from ..services.client_service import ClientService
        result = ClientService.reset_ai(request, self.get_object())
        return Response(result)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reset_workflows(self, request, pk=None):
        from ..services.client_service import ClientService
        result = ClientService.reset_workflows(request, self.get_object())
        return Response(result)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_feature(self, request, pk=None):
        from ..services.client_service import ClientService
        feature = request.data.get('feature')
        result = ClientService.toggle_feature(request, self.get_object(), feature)
        if "error" in result:
            return Response({"error": result["error"]}, status=result["status_code"])
        return Response({"status": result["status"], "value": result["value"]})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_whatsapp_profile_picture(self, request, pk=None):
        client = self.get_object()
        
        # Verify ownership
        if request.user.role != 'ADMIN' and request.user.client_id != client.id:
            return Response({"error": "Unauthorized"}, status=403)

        if not client.whatsapp_phone_number_id or not client.whatsapp_access_token:
            return Response({"error": "WhatsApp not connected"}, status=400)

        image_file = request.FILES.get('profile_picture')
        if not image_file:
            return Response({"error": "No image provided. Please send file in 'profile_picture' form field."}, status=400)

        app_id = os.getenv('FACEBOOK_APP_ID')
        if not app_id:
            return Response({"error": "Server is missing FACEBOOK_APP_ID"}, status=500)

        file_length = image_file.size
        file_type = image_file.content_type

        # 1. Create Resumable Upload Session
        session_url = f"https://graph.facebook.com/{os.getenv('WHATSAPP_API_VERSION', 'v20.0')}/{app_id}/uploads?file_length={file_length}&file_type={file_type}"
        headers = {
            "Authorization": f"Bearer {client.whatsapp_access_token}"
        }
        
        try:
            res = requests.post(session_url, headers=headers)
            res_data = res.json()
            if 'id' not in res_data:
                return Response({"error": "Failed to create upload session with Meta", "details": res_data}, status=400)
                
            upload_session_id = res_data['id']

            # 2. Upload file binary data
            upload_url = f"https://graph.facebook.com/{os.getenv('WHATSAPP_API_VERSION', 'v20.0')}/{upload_session_id}"
            upload_headers = {
                "Authorization": f"Bearer {client.whatsapp_access_token}",
                "file_offset": "0"
            }
            
            image_file.seek(0)
            upload_res = requests.post(upload_url, headers=upload_headers, data=image_file.read())
            upload_data = upload_res.json()
            if 'h' not in upload_data:
                return Response({"error": "Failed to upload file data to Meta", "details": upload_data}, status=400)
                
            file_handle = upload_data['h']

            # 3. Update WhatsApp Business Profile
            profile_url = f"https://graph.facebook.com/{os.getenv('WHATSAPP_API_VERSION', 'v20.0')}/{client.whatsapp_phone_number_id}/whatsapp_business_profile"
            profile_payload = {
                "messaging_product": "whatsapp",
                "profile_picture_handle": file_handle
            }
            profile_headers = {
                "Authorization": f"Bearer {client.whatsapp_access_token}",
                "Content-Type": "application/json"
            }
            profile_res = requests.post(profile_url, headers=profile_headers, json=profile_payload)
            profile_data = profile_res.json()

            if profile_res.status_code == 200 and profile_data.get('success'):
                return Response({"status": "success", "message": "Profile picture updated successfully on WhatsApp!"})
            else:
                return Response({"error": "Failed to update WhatsApp profile", "details": profile_data}, status=400)
                
        except Exception as e:
            return Response({"error": f"An internal error occurred: {str(e)}"}, status=500)


class ContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsApprovedUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            from ..serializers import ContactListSerializer
            return ContactListSerializer
        from ..serializers import ContactSerializer
        return ContactSerializer

    def get_queryset(self):
        client = get_tenant_client(self.request)
        if not client:
            return Contact.objects.none()

        allowed_channels = get_user_allowed_channels(self.request.user, client)
        if not allowed_channels and self.request.user.role != 'ADMIN':
            return Contact.objects.none()

        qs = ContactRepository.filter_contacts(client=client)

        search_query = self.request.query_params.get('search', None)
        if search_query:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search_query) | Q(phone_number__icontains=search_query) | Q(platform_id__icontains=search_query))

        channel_filter = self.request.query_params.get('preferred_channel', None)
        from ..models import Conversation, Message
        from django.db.models import Q

        if channel_filter and channel_filter != 'ALL':
            target_channels = [channel_filter.upper()]
        else:
            target_channels = allowed_channels

        allowed_convos = list(Conversation.objects.filter(
            client=client, 
            channel__in=target_channels
        ).values_list('contact_platform_id', flat=True).distinct())

        allowed_msg_from = list(Message.objects.filter(
            client=client, 
            channel__in=target_channels
        ).values_list('from_address', flat=True).distinct())

        allowed_msg_to = list(Message.objects.filter(
            client=client, 
            channel__in=target_channels
        ).values_list('to_address', flat=True).distinct())

        allowed_channel_contact_ids = list(set(allowed_convos + allowed_msg_from + allowed_msg_to))

        if channel_filter and channel_filter != 'ALL':
            if channel_filter.upper() == 'INSTAGRAM':
                qs = qs.filter(
                    Q(platform_id__in=allowed_channel_contact_ids) | 
                    Q(preferred_channel='INSTAGRAM') |
                    Q(name__icontains='INSTAGRAM')
                )
            elif channel_filter.upper() == 'FACEBOOK':
                qs = qs.filter(
                    Q(platform_id__in=allowed_channel_contact_ids) | 
                    Q(preferred_channel='FACEBOOK') |
                    Q(name__icontains='FACEBOOK')
                )
            elif channel_filter.upper() == 'GMAIL':
                qs = qs.filter(
                    Q(platform_id__in=allowed_channel_contact_ids) | 
                    Q(preferred_channel='GMAIL') |
                    Q(platform_id__contains='@')
                )
            elif channel_filter.upper() == 'WHATSAPP':
                qs = qs.filter(
                    Q(platform_id__in=allowed_channel_contact_ids) | 
                    Q(preferred_channel='WHATSAPP') |
                    (
                        ~Q(name__icontains='INSTAGRAM') & 
                        ~Q(name__icontains='FACEBOOK') & 
                        ~Q(platform_id__contains='@')
                    )
                )
            else:
                qs = qs.filter(platform_id__in=allowed_channel_contact_ids)
        else:
            # If viewing ALL, show all contacts in allowed channels OR all workspace contacts
            if set(allowed_channels) < {'WHATSAPP', 'FACEBOOK', 'INSTAGRAM'}:
                qs = qs.filter(
                    Q(platform_id__in=allowed_channel_contact_ids) |
                    Q(preferred_channel__in=allowed_channels)
                )

        return qs

    def perform_create(self, serializer):
        client = get_tenant_client(self.request)
        instance = serializer.save(client=client)
        AdminService.log_admin_action(self.request, instance, 'Contacts', 'CREATE', after_value=str(serializer.data))

    def perform_update(self, serializer):
        before_instance = self.get_object()
        before_data = str(self.get_serializer(before_instance).data)
        instance = serializer.save()
        AdminService.log_admin_action(self.request, instance, 'Contacts', 'UPDATE', before_value=before_data, after_value=str(serializer.data))

    def perform_destroy(self, instance):
        before_data = str(self.get_serializer(instance).data)
        AdminService.log_admin_action(self.request, instance, 'Contacts', 'DELETE', before_value=before_data)
        instance.delete()

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        client = get_tenant_client(request)
        if not client:
            return Response({"message": "No client associated"}, status=400)
            
        file = request.FILES.get('file')
        if not file or not file.name.endswith('.csv'):
            return Response({"message": "Please upload a valid CSV file."}, status=400)
            
        try:
            from ..services.contact_service import ContactService
            result = ContactService.import_contacts_from_csv(client, file, request.data.get('stage', 'NEW'))
            return Response(result)
        except Exception as e:
            return Response({"message": f"Error parsing CSV: {str(e)}"}, status=400)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        client = get_tenant_client(request)
        if not client:
            return Response({"message": "No client associated"}, status=400)
            
        from ..services.contact_service import ContactService
        return ContactService.export_contacts_to_csv(client)


class ClientStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = getattr(request.user, 'client', None)
        if not client:
            return Response({
                "totalConversations": 0,
                "automationRuns": 0,
                "activeUsers": 0,
                "avgResponse": "14s",
                "resourceCounts": {
                    "connectors": 0,
                    "projects": 0,
                    "teamMembers": 0,
                    "pdfs": 0,
                    "products": 0
                }
            }, status=200)
            
        # Avoid slow distinct() aggregation queries in Djongo
        # total_conversations = MessageRepository.filter_messages(client=client).values('from_address', 'to_address').distinct().count()
        total_conversations = ContactRepository.filter_contacts(client=client).count()
        automation_runs = MessageRepository.filter_messages(client=client, message_type='OUTGOING', status='SENT').count()
        active_users = total_conversations

        # --- Live Resource Counts from Database ---
        # Connectors: count how many channel flags are enabled on this client
        connector_flags = [
            client.automation_enabled and bool(client.whatsapp_access_token),  # WhatsApp
            client.facebook_enabled,
            client.instagram_enabled,
            client.gmail_enabled,
            client.outlook_enabled,
            client.youtube_enabled,
            client.google_news_enabled,
            client.onedrive_enabled,
            client.google_calendar_enabled,
            client.google_sheets_enabled,
            client.google_docs_enabled,
            client.google_slides_enabled,
            client.zoho_enabled,
        ]
        connectors_count = sum(1 for flag in connector_flags if flag)

        # Workflows count
        from ..repositories.workflow_repository import WorkflowRepository
        projects_count = WorkflowRepository.filter_workflows(client=client).count()

        # Team Members: users linked to this client
        from ..models import User
        team_members_count = User.objects.filter(client=client).count()

        # Knowledge PDFs
        from ..repositories.knowledge_repository import KnowledgeRepository
        pdfs_count = KnowledgeRepository.filter_documents(client=client).count()

        # Products
        from ..repositories.product_repository import ProductRepository
        products_count = ProductRepository.filter_products(client=client).count()
        return Response({
            "totalConversations": total_conversations,
            "automationRuns": automation_runs,
            "activeUsers": active_users,
            "avgResponse": "14s",
            "resourceCounts": {
                "connectors": connectors_count,
                "projects": projects_count,
                "teamMembers": team_members_count,
                "pdfs": pdfs_count,
                "products": products_count
            }
        })


class SuggestDraftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = get_tenant_client(request)
        if not client:
            return Response({"error": "No client associated"}, status=400)
            
        contact_id = request.data.get('contact_id')
        if not contact_id:
            return Response({"error": "contact_id is required"}, status=400)
            
        # Get last 10 messages for context
        try:
            contact = ContactRepository.get_contact(id=contact_id, client=client)
        except Contact.DoesNotExist:
            return Response({"error": "Contact not found"}, status=404)
            
        messages = MessageRepository.filter_messages(
            client=client, 
            from_address=contact.platform_id
        ) | MessageRepository.filter_messages(
            client=client, 
            to_address=contact.platform_id
        )
        
        messages = messages.order_by('-created_at')[:10]
        messages = reversed(messages) # chronological order
        
        chat_history = []
        for msg in messages:
            # Internal notes aren't strictly part of the external convo, but could be helpful context.
            # Let's include them for AI context.
            role = "user" if msg.message_type == "INCOMING" else "assistant"
            chat_history.append({"role": role, "content": msg.body})
            
        if not chat_history:
            return Response({"draft": "Hi there! How can I help you today?"})
            
        draft = get_ai_draft(chat_history)
        return Response({"draft": draft})


class ClientMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = get_tenant_client(request)
        if not client:
            return Response([])

        allowed_channels = get_user_allowed_channels(request.user, client)
        if not allowed_channels and request.user.role != 'ADMIN':
            return Response([])
            
        contact_id = request.query_params.get('contact_id')
        try:
            limit = int(request.query_params.get('limit', 100))
        except ValueError:
            limit = 100
            
        try:
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            offset = 0

        messages = MessageRepository.filter_messages(client=client)

        channel_filter = request.query_params.get('channel')
        if channel_filter and channel_filter != 'ALL':
            if channel_filter.upper() in allowed_channels or request.user.role == 'ADMIN':
                messages = messages.filter(channel=channel_filter.upper())
            else:
                return Response([])
        else:
            if request.user.role != 'ADMIN':
                messages = messages.filter(channel__in=allowed_channels)

        if contact_id:
            from django.db.models import Q
            messages = messages.filter(Q(from_address=contact_id) | Q(to_address=contact_id))

        # Sort descending to get latest messages
        messages = messages.order_by('-created_at')[offset:offset+limit]
        
        data = []
        for msg in messages:
            data.append({
                "id": str(msg.id),
                "from_address": msg.from_address,
                "to_address": msg.to_address,
                "body": msg.body,
                "channel": msg.channel,
                "message_type": msg.message_type,
                "status": msg.status,
                "buttons": getattr(msg, 'buttons', []) or [],
                "metadata": msg.metadata or {},
                "created_at": msg.created_at
            })
        return Response(data)


    def post(self, request):
        client = get_tenant_client(request)
        if not client:
            return Response({"error": "No client associated"}, status=400)
            
        to_number = request.data.get('to_number')
        body = request.data.get('body')
        channel = request.data.get('channel')
        
        if not to_number or not body:
            return Response({"error": "to_number and body are required"}, status=400)
            
        message_type = request.data.get('message_type', 'OUTGOING')
        
        if message_type == 'INTERNAL':
            new_msg = MessageRepository.create_message(
                client=client,
                channel=channel or 'WHATSAPP',
                from_address=client.business_name,
                to_address=to_number,
                body=body,
                message_type='INTERNAL',
                status='SENT'
            )
            return Response({
                "id": str(new_msg.id),
                "from_address": new_msg.from_address,
                "to_address": new_msg.to_address,
                "body": new_msg.body,
                "channel": new_msg.channel,
                "message_type": new_msg.message_type,
                "status": new_msg.status,
                "buttons": getattr(new_msg, 'buttons', []) or [],
                "metadata": new_msg.metadata or {},
                "created_at": new_msg.created_at
            })
            
        # Detect channel if not provided
        if not channel:
            last_msg = MessageRepository.filter_messages(client=client, from_address=to_number).order_by('-created_at').first()
            if not last_msg:
                last_msg = MessageRepository.filter_messages(client=client, to_address=to_number).order_by('-created_at').first()
            channel = last_msg.channel if last_msg else 'WHATSAPP'
            
        channel = channel.upper()
        
        # Human agent takeover: Pause bot response for this contact
        try:
            from ..models import Contact
            # Standardize format for query lookup
            formatted_number = to_number.replace('+', '').strip()
            contact = ContactRepository.filter_contacts(
                client=client, 
                phone_number__icontains=formatted_number
            ).first()
            if not contact:
                contact = ContactRepository.filter_contacts(
                    client=client, 
                    platform_id=to_number
                ).first()
            if contact and not contact.bot_paused:
                contact.bot_paused = True
                contact.save()
        except Exception as e:
            print(f"Failed to auto-pause bot for contact: {str(e)}")
        
        new_msg = None
        
        if channel == 'WHATSAPP':
            phone_number_id = client.whatsapp_phone_number_id or 'WHATSAPP_SYSTEM'
            webhook_view = WhatsAppWebhookView()
            try:
                new_msg = webhook_view.send_whatsapp_message(client, to_number, body, phone_number_id)
            except Exception as _werr:
                new_msg = MessageRepository.create_message(
                    client=client,
                    channel='WHATSAPP',
                    from_address=phone_number_id,
                    to_address=to_number,
                    body=body,
                    message_type='OUTGOING',
                    status='SENT'
                )
        elif channel in ['INSTAGRAM', 'FACEBOOK']:
            webhook_view = FacebookInstagramWebhookView()
            try:
                new_msg = webhook_view.send_message(client, channel, to_number, body)
            except Exception as _ferr:
                new_msg = MessageRepository.create_message(
                    client=client,
                    channel=channel,
                    from_address=channel,
                    to_address=to_number,
                    body=body,
                    message_type='OUTGOING',
                    status='SENT'
                )
        elif channel == 'GMAIL':
            from ..services.gmail_service import send_gmail_message
            try:
                send_gmail_message(client, to_number, body)
                new_msg = MessageRepository.create_message(
                    client=client,
                    channel='GMAIL',
                    from_address=client.gmail_config.get('email_address', ''),
                    to_address=to_number,
                    body=body,
                    message_type='OUTGOING',
                    status='SENT'
                )
            except Exception as e:
                return Response({"error": str(e)}, status=400)
        else:
            return Response({"error": f"Unsupported channel: {channel}"}, status=400)
            
        if new_msg:
            return Response({
                "id": str(new_msg.id),
                "from_address": new_msg.from_address,
                "to_address": new_msg.to_address,
                "body": new_msg.body,
                "channel": new_msg.channel,
                "message_type": new_msg.message_type,
                "status": new_msg.status,
                "buttons": getattr(new_msg, 'buttons', []) or [],
                "metadata": new_msg.metadata or {},
                "created_at": new_msg.created_at
            })
            
        return Response({"status": "sent"})

class MediaProxyView(APIView):
    """Proxy endpoint to stream WhatsApp/Meta media files to the frontend with correct Content-Type."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        media_id = request.query_params.get('media_id')
        media_url = request.query_params.get('media_url')
        
        client = get_tenant_client(request)
        if not client:
            client = Client.objects.filter(whatsapp_access_token__isnull=False).exclude(whatsapp_access_token='').first()

        token = client.whatsapp_access_token if client else None
        if media_id and token:
            try:
                url_res = requests.get(
                    f"https://graph.facebook.com/v18.0/{media_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                if url_res.status_code == 200:
                    media_url = url_res.json().get('url')
            except Exception as e:
                logger.error("Failed to get media URL for %s: %s", media_id, e)

        if media_url:
            try:
                headers = {"Authorization": f"Bearer {token}"} if (token and "facebook.com" in media_url) else {}
                file_res = requests.get(media_url, headers=headers, timeout=30)
                if file_res.status_code == 200:
                    content_type = file_res.headers.get('Content-Type', 'application/octet-stream')
                    from django.http import HttpResponse
                    response = HttpResponse(file_res.content, content_type=content_type)
                    filename = request.query_params.get('filename')
                    if filename:
                        response['Content-Disposition'] = f'inline; filename="{filename}"'
                    return response
            except Exception as e:
                logger.error("Failed downloading media from %s: %s", media_url, e)

        return Response({"error": "Media file not found or download failed."}, status=404)

class AuditLogMixin:
    def get_module_name(self):
        model = None
        if hasattr(self, 'queryset') and self.queryset:
            model = self.queryset.model
        elif hasattr(self, 'get_queryset'):
            try:
                model = self.get_queryset().model
            except Exception:
                pass
        return model.__name__ if model else "General"

    def perform_create(self, serializer):
        instance = serializer.save()
        AdminService.log_admin_action(self.request, instance, self.get_module_name(), 'CREATE', after_value=str(serializer.data))
        
    def perform_update(self, serializer):
        before_instance = self.get_object()
        before_data = str(self.get_serializer(before_instance).data)
        instance = serializer.save()
        AdminService.log_admin_action(self.request, instance, self.get_module_name(), 'UPDATE', before_value=before_data, after_value=str(serializer.data))
        
    def perform_destroy(self, instance):
        before_data = str(self.get_serializer(instance).data)
        AdminService.log_admin_action(self.request, instance, self.get_module_name(), 'DELETE', before_value=before_data)
        instance.delete()


