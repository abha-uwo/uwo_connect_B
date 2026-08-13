import os
import requests

def get_zoho_auth_url(redirect_uri, scope="ZohoCRM.modules.ALL", access_type="offline", prompt="consent"):
    client_id = os.environ.get("ZOHO_CLIENT_ID", "")
    domain = os.environ.get("ZOHO_DOMAIN", "com")
    
    auth_url = f"https://accounts.zoho.{domain}/oauth/v2/auth"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "access_type": access_type,
        "prompt": prompt
    }
    
    # Construct URL manually to avoid URL encoding issues with scopes
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{auth_url}?{query_string}"

def exchange_zoho_code(code, redirect_uri):
    client_id = os.environ.get("ZOHO_CLIENT_ID", "")
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET", "")
    domain = os.environ.get("ZOHO_DOMAIN", "com")
    
    token_url = f"https://accounts.zoho.{domain}/oauth/v2/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    return response.json()

def refresh_zoho_token(client):
    """Refreshes the Zoho access token and saves it to the client object."""
    if not client.zoho_config or 'refresh_token' not in client.zoho_config:
        raise Exception("No refresh token available")
        
    client_id = os.environ.get("ZOHO_CLIENT_ID", "")
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET", "")
    domain = os.environ.get("ZOHO_DOMAIN", "com")
    
    token_url = f"https://accounts.zoho.{domain}/oauth/v2/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": client.zoho_config['refresh_token']
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    
    if 'access_token' in token_data:
        client.zoho_config['access_token'] = token_data['access_token']
        # The API might not return a new refresh token, so keep the old one
        if 'refresh_token' in token_data:
            client.zoho_config['refresh_token'] = token_data['refresh_token']
        
        client.save()
        
    return token_data.get('access_token')

def create_zoho_lead(client, lead_data):
    """Creates a Lead in Zoho CRM. Automatically refreshes token if expired."""
    if not client.zoho_enabled or not client.zoho_config or 'access_token' not in client.zoho_config:
        raise Exception("Zoho is not connected or configured properly.")
        
    domain = os.environ.get("ZOHO_DOMAIN", "com")
    api_url = f"https://www.zohoapis.{domain}/crm/v3/Leads"
    
    access_token = client.zoho_config['access_token']
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "data": [lead_data]
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    
    # If unauthorized, try to refresh token once
    if response.status_code == 401:
        new_access_token = refresh_zoho_token(client)
        headers["Authorization"] = f"Zoho-oauthtoken {new_access_token}"
        response = requests.post(api_url, headers=headers, json=payload)
        
    response.raise_for_status()
    return response.json()
