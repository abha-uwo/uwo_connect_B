from ..permissions.custom_permissions import IsApprovedUser
from rest_framework import status, views, viewsets
from rest_framework.response import Response
from firebase_admin import auth as firebase_auth
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..serializers import RegisterSerializer, UserSerializer, ClientSerializer, AutomationSerializer, WorkflowSerializer, ContactSerializer, TemplateSerializer, CampaignSerializer, SupportMessageSerializer, AuditLogSerializer, TeamInviteSerializer, ProductSerializer, OrderSerializer
from ..repositories.client_repository import ClientRepository
from ..models import User, Client, Automation, Message, Workflow, KnowledgeDocument, KnowledgeChunk, Contact, Template, Campaign, SupportMessage, AuditLog, TeamInvite, Product, Order
import requests
import os
import json
from ..services.ai_service import get_ai_response, get_platform_assistance, get_rag_response, get_embedding, chunk_text, find_relevant_chunks
from rest_framework.permissions import BasePermission

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

class RegisterView(views.APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, req):
        serializer = RegisterSerializer(data=req.data)
        if serializer.is_valid():
            from ..services.auth_service import AuthService
            result = AuthService.register_user(serializer)
            if result.get("status") == "APPROVED":
                return Response({
                    "user": result["user"],
                    "token": result["token"]
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "message": result["message"],
                    "userId": result["userId"]
                }, status=status.HTTP_201_CREATED)
            
        first_error = next(iter(serializer.errors.values()))[0]
        return Response({"message": str(first_error)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')


class LoginView(views.APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, req):
        email = req.data.get('email', '').strip().lower()
        password = req.data.get('password', '')

        from ..services.auth_service import AuthService
        result = AuthService.login_user(email, password)
        
        if "error" in result:
            return Response({"message": result["error"]}, status=result["status_code"])

        return Response({
            "user": result["user"],
            "token": result["token"]
        })

@method_decorator(csrf_exempt, name='dispatch')


class GoogleLoginView(views.APIView):
    """Legacy Google login — kept for backward compatibility."""
    permission_classes = []
    authentication_classes = []

    def post(self, req):
        return Response({"message": "Please use Firebase authentication. This endpoint is deprecated."}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')


class GoogleClientIdView(views.APIView):
    """Legacy Google Client ID endpoint — kept for backward compatibility."""
    permission_classes = []
    authentication_classes = []

    def get(self, req):
        return Response({"client_id": ""})

@method_decorator(csrf_exempt, name='dispatch')


class FirebaseLoginView(views.APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, req):
        id_token = req.data.get('id_token', '').strip()
        name = req.data.get('name', '').strip()
        invite_token = req.data.get('invite_token', '').strip()
        business_name = req.data.get('business_name', '').strip()

        from ..services.auth_service import AuthService
        result = AuthService.process_firebase_login(id_token, name, invite_token, business_name)

        if "error" in result:
            return Response({"message": result["error"]}, status=result["status_code"])

        if result.get("is_created"):
            if result.get("status") == "PENDING":
                return Response({
                    "message": result["message"],
                    "userId": result["userId"]
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "user": result["user"],
                    "token": result["token"]
                }, status=status.HTTP_201_CREATED)

        return Response({
            "user": result["user"],
            "token": result["token"]
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.client:
            return Response({"message": "No client associated"}, status=404)
        serializer = ClientSerializer(request.user.client)
        return Response({
            "client": serializer.data,
            "user": {
                "name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                "email": request.user.email,
            }
        })

    def patch(self, request):
        if not request.user.client:
            return Response({"message": "No client associated"}, status=404)
        
        # Update User fields if provided
        user = request.user
        if 'name' in request.data:
            name_parts = request.data['name'].split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.save()

        # Update Client fields
        serializer = ClientSerializer(request.user.client, data=request.data, partial=True)
        if serializer.is_valid():
            client_instance = serializer.save()
            
            # --- Programmatic Webhook Auto-Subscription to Meta App ---
            import requests
            
            # 1. Handle Facebook Page Subscription
            facebook_config = request.data.get('facebook_config')
            if facebook_config and isinstance(facebook_config, dict):
                page_id = facebook_config.get('page_id')
                access_token = facebook_config.get('access_token')
                if page_id and access_token:
                     try:
                         sub_url = f"https://graph.facebook.com/v20.0/{page_id}/subscribed_apps"
                         sub_payload = {
                             "subscribed_fields": "messages,messaging_postbacks,messaging_optins,message_deliveries",
                             "access_token": access_token
                         }
                         res = requests.post(sub_url, data=sub_payload, timeout=10)
                         print(f"\nfrom ..repositories.campaign_repository import TemplateRepository\nfrom ..repositories.campaign_repository import CampaignRepository\nfrom ..repositories.system_repository import SystemRepository\nfrom ..repositories.message_repository import SupportMessageRepository\nfrom ..repositories.client_repository import ClientRepository\nfrom ..repositories.user_repository import TeamInviteRepository\nfrom ..repositories.user_repository import UserRepository\nfrom ..repositories.automation_repository import WorkflowRepository\nfrom ..repositories.message_repository import TeamMessageRepository\nfrom ..repositories.message_repository import MessageRepository\nfrom ..repositories.knowledge_repository import KnowledgeRepository\nfrom ..repositories.automation_repository import AutomationRepository\nfrom ..repositories.contact_repository import ContactRepository\n\n[Meta API] Facebook Page {page_id} Webhook Subscription Response: {res.status_code} {res.text}\n")
                     except Exception as e:
                         print(f"Error subscribing Facebook page {page_id}: {str(e)}")
            
            # 2. Handle Instagram Page Subscription
            instagram_config = request.data.get('instagram_config')
            if instagram_config and isinstance(instagram_config, dict):
                access_token = instagram_config.get('access_token')
                if access_token:
                    try:
                        # Find Page ID associated with the Instagram access token / Page Access Token
                        me_res = requests.get(f"https://graph.facebook.com/v20.0/me?fields=id,name&access_token={access_token}", timeout=10)
                        if me_res.status_code == 200:
                            page_id = me_res.json().get('id')
                            if page_id:
                                sub_url = f"https://graph.facebook.com/v20.0/{page_id}/subscribed_apps"
                                sub_payload = {
                                    "subscribed_fields": "messages,messaging_postbacks,messaging_optins,message_deliveries",
                                    "access_token": access_token
                                }
                                res = requests.post(sub_url, data=sub_payload, timeout=10)
                                print(f"\n[Meta API] Instagram linked Facebook Page {page_id} Webhook Subscription Response: {res.status_code} {res.text}\n")
                    except Exception as e:
                         print(f"Error subscribing Instagram linked page: {str(e)}")
                         
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

from ..models import User, Client, Automation, Workflow, GlobalSetting
from ..serializers import RegisterSerializer, UserSerializer, ClientSerializer, AutomationSerializer, WorkflowSerializer, GlobalSettingSerializer


class ForgotPasswordSendOTPView(views.APIView):
    permission_classes = []

    def post(self, req):
        email = req.data.get('email', '').lower().strip()
        from ..services.auth_service import AuthService
        result = AuthService.forgot_password_send_otp(email)
        return Response({"message": result.get("message")}, status=result.get("status_code", 200))

@method_decorator(csrf_exempt, name='dispatch')


class ForgotPasswordVerifyOTPView(views.APIView):
    permission_classes = []

    def post(self, req):
        email = req.data.get('email', '').lower().strip()
        otp = req.data.get('otp', '').strip()
        
        from ..services.auth_service import AuthService
        result = AuthService.forgot_password_verify_otp(email, otp)
        return Response({"message": result.get("message")}, status=result.get("status_code", 200))

@method_decorator(csrf_exempt, name='dispatch')


class ForgotPasswordResetView(views.APIView):
    permission_classes = []

    def post(self, req):
        email = req.data.get('email', '').lower().strip()
        password = req.data.get('password', '')
        
        from ..services.auth_service import AuthService
        result = AuthService.forgot_password_reset(email, password)
        return Response({"message": result.get("message")}, status=result.get("status_code", 200))

class WhatsAppEmbeddedSignupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=400)

        import os
        import requests
        
        client_id = os.getenv('FACEBOOK_APP_ID')
        client_secret = os.getenv('FACEBOOK_APP_SECRET')
        
        if not client_id or not client_secret:
            return Response({"error": "Facebook App credentials not configured on server."}, status=500)

        # 1. Exchange code for access token
        token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        }
        
        token_res = requests.get(token_url, params=token_payload)
        token_data = token_res.json()
        
        if "error" in token_data:
            return Response({"error": "Failed to exchange code", "details": token_data}, status=400)
            
        access_token = token_data.get('access_token')
        
        # 2. Get shared WABA info from the embedded signup callback
        # In the embedded signup flow, Meta gives us shared WABA IDs 
        waba_url = f"https://graph.facebook.com/v20.0/me/client_whatsapp_business_accounts?access_token={access_token}"
        waba_res = requests.get(waba_url)
        waba_data = waba_res.json()
        
        if "error" in waba_data or not waba_data.get('data'):
            return Response({"error": "Could not find WhatsApp Business Accounts", "details": waba_data}, status=400)
            
        waba_id = waba_data['data'][0]['id']
        
        # 3. Get Phone Number ID
        phone_url = f"https://graph.facebook.com/v20.0/{waba_id}/phone_numbers?access_token={access_token}"
        phone_res = requests.get(phone_url)
        phone_data = phone_res.json()
        
        if "error" in phone_data or not phone_data.get('data'):
            return Response({"error": "Could not find Phone Numbers for WABA", "details": phone_data}, status=400)
            
        phone_number_id = phone_data['data'][0]['id']
        display_phone_number = phone_data['data'][0].get('display_phone_number', '')
        
        # 4. Save to Client
        client = request.user.client
        client.whatsapp_config = {
            "access_token": access_token,
            "waba_id": waba_id,
            "phone_number_id": phone_number_id,
            "display_phone_number": display_phone_number
        }
        client.whatsapp_access_token = access_token
        client.whatsapp_waba_id = waba_id
        client.whatsapp_phone_number_id = phone_number_id
        client.phone_number = display_phone_number
        client.whatsapp_enabled = True
        client.save()
        
        return Response({
            "message": "WhatsApp Business connected successfully",
            "whatsapp_config": client.whatsapp_config
        })


class InstagramEmbeddedSignupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.data.get('access_token')

        import os
        import requests
        import datetime
        
        client_id = os.getenv('FACEBOOK_APP_ID')
        client_secret = os.getenv('FACEBOOK_APP_SECRET')
        
        if not client_id or not client_secret:
            return Response({"error": "Facebook App credentials not configured on server."}, status=500)

        if not access_token:
            return Response({"error": "No access_token provided"}, status=400)

        # Exchange for Long-Lived Token
        ll_res = requests.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "grant_type":        "fb_exchange_token",
                "client_id":         client_id,
                "client_secret":     client_secret,
                "fb_exchange_token": access_token,
            }
        )
        ll_data = ll_res.json()
        long_lived_token = ll_data.get("access_token", access_token)
        
        # Fetch connected pages and their Instagram accounts
        accounts_url = f"https://graph.facebook.com/v20.0/me/accounts?fields=id,name,access_token,instagram_business_account{{id,username,name}}&access_token={long_lived_token}"
        accounts_res = requests.get(accounts_url)
        accounts_data = accounts_res.json()
        
        if "error" in accounts_data or not accounts_data.get('data'):
            return Response({"error": "Could not find connected Facebook Pages", "details": accounts_data}, status=400)
            
        # Find the first page that has an Instagram Business Account attached
        ig_account = None
        page_access_token = long_lived_token
        fb_page_id = None
        fb_page_name = None
        
        for page in accounts_data['data']:
            if 'instagram_business_account' in page:
                ig_account = page['instagram_business_account']
                page_access_token = page.get('access_token', long_lived_token)
                fb_page_id = page['id']
                fb_page_name = page.get('name')
                break
                
        if not ig_account:
            return Response({"error": "No linked Instagram Business Account found on your Facebook Pages. Please link your Instagram account to your Facebook Page first."}, status=400)

        client = request.user.client
        
        # Save Instagram config
        client.instagram_config = {
            "access_token": page_access_token,
            "instagram_business_id": ig_account['id'],
            "page_id": fb_page_id,
            "page_name": ig_account.get('username', ig_account.get('name', 'Instagram Account')),
            "last_connected": datetime.datetime.utcnow().isoformat(),
            "last_updated": datetime.datetime.utcnow().isoformat(),
        }
        client.instagram_enabled = True
        
        # Save Facebook config since we have it
        client.facebook_config = {
            "access_token": page_access_token,
            "page_id": fb_page_id,
            "page_name": fb_page_name,
            "last_connected": datetime.datetime.utcnow().isoformat(),
            "last_updated": datetime.datetime.utcnow().isoformat(),
        }
        client.facebook_enabled = True
        
        client.save()
        
        return Response({
            "message": "Instagram connected successfully via Facebook",
            "instagram_config": client.instagram_config,
            "facebook_config": client.facebook_config
        })

class FacebookEmbeddedSignupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        access_token = request.data.get('access_token')

        import os
        import requests
        
        client_id = os.getenv('FACEBOOK_APP_ID')
        client_secret = os.getenv('FACEBOOK_APP_SECRET')
        
        if not client_id or not client_secret:
            return Response({"error": "Facebook App credentials not configured on server."}, status=500)

        long_lived_token = None

        if code:
            token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
            token_payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "https://uwoconnect.aisa24.com/client/channels",
                "code": code
            }
            token_res = requests.get(token_url, params=token_payload)
            token_data = token_res.json()
            if "error" in token_data:
                return Response({"error": "Failed to exchange code", "details": token_data}, status=400)
            long_lived_token = token_data.get('access_token')
        elif access_token:
            ll_res = requests.get(
                "https://graph.facebook.com/v20.0/oauth/access_token",
                params={
                    "grant_type":        "fb_exchange_token",
                    "client_id":         client_id,
                    "client_secret":     client_secret,
                    "fb_exchange_token": access_token,
                }
            )
            ll_data = ll_res.json()
            long_lived_token = ll_data.get("access_token", access_token)
        else:
            return Response({"error": "No code or access_token provided"}, status=400)
            
        accounts_url = f"https://graph.facebook.com/v20.0/me/accounts?fields=id,name,access_token,category&access_token={long_lived_token}"
        accounts_res = requests.get(accounts_url)
        accounts_data = accounts_res.json()
        
        if "error" in accounts_data or not accounts_data.get('data'):
            return Response({"error": "Could not find connected Facebook Pages", "details": accounts_data}, status=400)
            
        page = accounts_data['data'][0]
        fb_page_id = page['id']
        fb_page_name = page.get('name', 'Facebook Page')
        page_access_token = page.get('access_token', long_lived_token)
        
        import datetime
        client = request.user.client
        client.facebook_config = {
            "access_token": page_access_token,
            "page_id": fb_page_id,
            "page_name": fb_page_name,
            "last_connected": datetime.datetime.utcnow().isoformat(),
            "last_updated": datetime.datetime.utcnow().isoformat(),
        }
        client.facebook_enabled = True
        client.save()
        
        return Response({
            "message": "Facebook Page connected successfully",
            "facebook_config": client.facebook_config
        })

class InstagramOAuthCallbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import datetime
        import requests
        import os
        code         = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')

        if not code:
            return Response({"error": "No code provided"}, status=400)
        if not redirect_uri:
            return Response({"error": "No redirect_uri provided"}, status=400)

        app_id     = os.getenv('INSTAGRAM_APP_ID') or os.getenv('FACEBOOK_APP_ID')
        app_secret = os.getenv('INSTAGRAM_APP_SECRET') or os.getenv('FACEBOOK_APP_SECRET')

        if not app_id or not app_secret:
            return Response({"error": "Instagram App credentials not configured on server."}, status=500)

        token_res = requests.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id":     app_id,
                "client_secret": app_secret,
                "grant_type":    "authorization_code",
                "redirect_uri":  redirect_uri,
                "code":          code,
            }
        )
        token_data = token_res.json()

        if "error_type" in token_data or "error" in token_data:
            return Response({"error": "Failed to exchange Instagram code", "details": token_data}, status=400)

        short_lived_token = token_data.get("access_token")
        instagram_user_id = token_data.get("user_id")

        if not short_lived_token:
            return Response({"error": "No access_token in Instagram response", "details": token_data}, status=400)

        ll_res = requests.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type":    "ig_exchange_token",
                "client_secret": app_secret,
                "access_token":  short_lived_token,
            }
        )
        ll_data = ll_res.json()
        long_lived_token = ll_data.get("access_token", short_lived_token)

        ig_res = requests.get(
            f"https://graph.instagram.com/v20.0/{instagram_user_id}",
            params={
                "fields":       "id,name,username,profile_picture_url,biography,website,followers_count",
                "access_token": long_lived_token,
            }
        )
        ig_data = ig_res.json()
        ig_username = ig_data.get("username", "")
        ig_name     = ig_data.get("name", ig_username)

        client = request.user.client
        client.instagram_config = {
            "instagram_business_id": str(instagram_user_id),
            "page_name":             ig_username or ig_name,
            "username":              ig_username,
            "access_token":          long_lived_token,
            "last_connected":        datetime.datetime.utcnow().isoformat(),
            "last_updated":          datetime.datetime.utcnow().isoformat(),
        }
        client.instagram_enabled = True
        client.save()

        return Response({
            "message": "Instagram Business Account connected successfully",
            "instagram_config": client.instagram_config,
        })
