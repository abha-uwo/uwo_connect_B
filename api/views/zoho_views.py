import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.utils import timezone
from api.models import Client
from api.services.zoho_service import get_zoho_auth_url, exchange_zoho_code, create_zoho_lead

class ZohoConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client
        if not client:
            return Response({"error": "User does not have an associated client."}, status=400)
            
        redirect_uri = os.environ.get("ZOHO_REDIRECT_URI", "http://localhost:8080/api/zoho/callback")
        
        # We can pass client.id in state for verification in callback
        state = str(client.id)
        
        authorization_url = get_zoho_auth_url(redirect_uri)
        # Append state
        authorization_url += f"&state={state}"
        
        # Save mapping from state to client_id in cache for 1 hour
        cache.set(f'zoho_state_{state}', client.id, timeout=3600)
        
        return Response({"url": authorization_url})

class ZohoCallbackView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        state = request.GET.get('state')
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        
        if error:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error={error}")
            
        if not state or not code:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error=missing_params")
            
        client_id = cache.get(f'zoho_state_{state}')
        if not client_id:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error=invalid_state")
            
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error=client_not_found")
            
        redirect_uri = os.environ.get("ZOHO_REDIRECT_URI", "http://localhost:8080/api/zoho/callback")
        
        try:
            tokens = exchange_zoho_code(code, redirect_uri)
        except Exception as e:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error=exchange_failed")
            
        if 'error' in tokens:
            return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_error={tokens['error']}")
            
        # Update client
        client.zoho_enabled = True
        client.zoho_config = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'api_domain': tokens.get('api_domain'),
            'token_type': tokens.get('token_type'),
            'expires_in': tokens.get('expires_in'),
            'connected_at': timezone.now().isoformat(),
            'domain': os.environ.get('ZOHO_DOMAIN', 'com')
        }
        client.save()
        
        return HttpResponseRedirect(f"{frontend_url}/client/channels?zoho_connected=true")

class ZohoDisconnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.user.client
        if not client:
            return Response({"error": "User does not have an associated client."}, status=400)
            
        client.zoho_enabled = False
        client.zoho_config = {}
        client.save()
        
        return Response({"success": True})

class ZohoTestLeadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.user.client
        if not client:
            return Response({"error": "User does not have an associated client."}, status=400)
            
        if not client.zoho_enabled:
            return Response({"error": "Zoho is not connected."}, status=400)
            
        lead_data = {
            "Last_Name": "Doe",
            "First_Name": "Test Lead",
            "Email": "test.lead@example.com",
            "Phone": "9876543210",
            "Company": "AISA Connect Demo",
            "Description": "This is an automated test lead from AISA Connect."
        }
        
        try:
            result = create_zoho_lead(client, lead_data)
            return Response({"success": True, "data": result})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
