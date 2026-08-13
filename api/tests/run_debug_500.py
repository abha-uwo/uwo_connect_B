import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from api.models import Client, Contact, SalesDocument, SalesDocumentItem, SalesDocumentActivity
from django.contrib.auth import get_user_model
from api.serializers import SalesDocumentSerializer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

User = get_user_model()

def test_create():
    client_workspace = Client.objects.first() # get any client
    user = User.objects.filter(client=client_workspace).first()
    if not user:
        user = User.objects.first()
        
    print(f"Using client: {client_workspace}, user: {user}")
    
    payload = {
        "document_type": "QUOTATION",
        "customer": None,
        "customer_name": "Abha",
        "customer_company": "",
        "customer_email": "abha@uwo24.com",
        "customer_phone": "",
        "billing_address": "jabalpur",
        "shipping_address": "",
        "tax_number": "",
        "document_date": "2026-08-12",
        "valid_until": "2026-08-27",
        "reference_number": "",
        "salesperson": None,
        "currency": "USD",
        "currency_symbol": "$",
        "customer_notes": "thanku",
        "internal_notes": "",
        "terms_conditions": "Terms...",
        "items": [
            {
                "name": "books",
                "sku": "reyyyyu",
                "unit": "pcs",
                "quantity": 1,
                "unit_price": 699,
                "discount_type": "PERCENTAGE",
                "discount_value": 50,
                "tax_rate": 18
            }
        ],
        "proposal_sections": []
    }
    
    # Simulate perform_create
    from api.views.sales_document_views import SalesDocumentViewSet
    from rest_framework.test import force_authenticate
    
    factory = APIRequestFactory()
    request = factory.post('/api/sales-documents/', payload, format='json')
    force_authenticate(request, user=user)
    
    view = SalesDocumentViewSet.as_view({'post': 'create'})
    try:
        response = view(request)
        print("Response status:", response.status_code)
        if hasattr(response, 'data'):
            print("Response data:", response.data)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create()
