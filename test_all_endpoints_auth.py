import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.urls import get_resolver
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
from api.models import User

def get_urls(resolver, prefix=''):
    urls = []
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            urls.extend(get_urls(pattern, prefix + str(pattern.pattern)))
        else:
            url = prefix + str(pattern.pattern)
            # Skip urls that require parameters
            if '<' not in url and '(?P<' not in url and '^' not in url:
                if not url.startswith('/'):
                    url = '/' + url
                urls.append(url)
    return urls

if __name__ == "__main__":
    print("Extracting URLs...")
    resolver = get_resolver()
    urls_to_test = get_urls(resolver)
    
    # Remove duplicates
    urls_to_test = list(set(urls_to_test))
    urls_to_test.sort()
    
    print(f"Found {len(urls_to_test)} static endpoints to test.")
    
    # Generate Token
    user = User.objects.filter(role='ADMIN').first()
    if not user:
        user = User.objects.first()
    
    if not user:
        print("No users found in database to generate token.")
        exit(1)
        
    print(f"Generating token for user: {user.email}")
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    
    # Test endpoints using APIClient
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    
    results = {}
    print("\nTesting Endpoints:")
    for url in urls_to_test:
        try:
            resp = client.get(url)
            status = resp.status_code
        except Exception as e:
            status = f"ERROR: {type(e).__name__}"
            
        print(f"[{status}] {url}")
        results[url] = status
        
    with open('endpoint_results_auth.txt', 'w') as f:
        for url, status in results.items():
            f.write(f"[{status}] {url}\n")
            
    print("\nResults saved to endpoint_results_auth.txt")
