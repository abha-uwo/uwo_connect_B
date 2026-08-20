import requests
import time
from concurrent.futures import ThreadPoolExecutor

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MjIzOTQ4LCJpYXQiOjE3ODcxMzc1NDgsImp0aSI6IjU0NTc1YWQ0MmUyZjQ2ZTNhMjQyYTdlMDM3NzczZjA1IiwidXNlcl9pZCI6IjZhMzhmOTJlM2E1MTdkZDkxNTljZTBjMCJ9.aROoQtB3PQ5GLzfXOsx93_hLKLIboSS5iNGDGo-vInU"
BASE_URL = "http://127.0.0.1:8080/api"

endpoints = [
    "/profile/",
    "/clients/",
    "/contacts/",
    "/conversations/",
    "/messages/",
    "/email/accounts/",
    "/email/messages/",
    "/email/analytics/",
    "/templates/",
    "/automations/",
    "/webrtc/call/active-check/",
    "/client/stats",
    "/team/members/",
    "/team/projects/",
    "/team/tasks/",
    "/sales/analytics/",
    "/sales-documents/",
    "/invoices/"
]

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def test_endpoint(endpoint):
    url = f"{BASE_URL}{endpoint}"
    start = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=20)
        elapsed = time.time() - start
        return endpoint, response.status_code, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return endpoint, "ERROR", elapsed

if __name__ == "__main__":
    print("Testing Endpoints Sequentially:")
    for ep in endpoints:
        ep, status, elapsed = test_endpoint(ep)
        print(f"{ep.ljust(30)} | Status: {str(status).ljust(5)} | Time: {elapsed:.2f}s")
