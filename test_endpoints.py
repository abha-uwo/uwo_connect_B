import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.urls import get_resolver

def get_urls(resolver, prefix=''):
    urls = []
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            urls.extend(get_urls(pattern, prefix + str(pattern.pattern)))
        else:
            url = prefix + str(pattern.pattern)
            # Skip urls that require parameters
            if '<' not in url and '(?P<' not in url and '^' not in url:
                urls.append('/' + url)
    return urls

if __name__ == "__main__":
    resolver = get_resolver()
    urls_to_test = get_urls(resolver)
    
    # Remove duplicates
    urls_to_test = list(set(urls_to_test))
    urls_to_test.sort()
    
    print(f"Found {len(urls_to_test)} static endpoints to test.")
    
    base_url = "http://127.0.0.1:8080"
    results = {}
    
    for url in urls_to_test:
        full_url = base_url + url
        try:
            # We use a short timeout and allow redirects.
            resp = requests.get(full_url, timeout=3)
            status = resp.status_code
        except requests.exceptions.RequestException as e:
            status = f"ERROR: {type(e).__name__}"
            
        print(f"[{status}] {full_url}")
        results[full_url] = status
        
    with open('endpoint_results.txt', 'w') as f:
        for url, status in results.items():
            f.write(f"[{status}] {url}\n")
            
    print("\nResults saved to endpoint_results.txt")
