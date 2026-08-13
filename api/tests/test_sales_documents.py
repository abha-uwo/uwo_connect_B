import uuid
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Client, Contact, SalesDocument, SalesDocumentItem, SalesDocumentActivity

User = get_user_model()

class SalesDocumentTests(APITestCase):
    def setUp(self):
        # Create client workspace
        self.client_workspace = Client.objects.create(
            business_name="Test Enterprise Ltd",
            email="test@enterprise.com",
            status="ACTIVE"
        )
        
        # Create normal test user
        self.user = User.objects.create_user(
            username="salestest",
            email="sales@test.com",
            password="password123",
            role="CLIENT",
            status="APPROVED",
            client=self.client_workspace
        )
        
        # Create a contact (customer)
        self.customer = Contact.objects.create(
            client=self.client_workspace,
            name="Jane Customer",
            email="jane@customer.com",
            phone_number="+15550199",
            stage="NEW"
        )
        
        # Log in
        self.client.login(username="salestest", password="password123")
        # For JWT, we can force authenticate
        self.client.force_authenticate(user=self.user)

    def test_create_quotation_and_verify_calculations(self):
        """
        Verify that creating a quotation calculates line totals, subtotals,
        tax amount, and grand total correctly.
        """
        url = "/api/sales-documents/"
        
        data = {
            "document_type": "QUOTATION",
            "customer": str(self.customer.id),
            "customer_name": self.customer.name,
            "customer_email": self.customer.email,
            "document_date": str(timezone.now().date()),
            "valid_until": str(timezone.now().date() + timezone.timedelta(days=15)),
            "currency": "USD",
            "additional_charges": "50.00",
            "items": [
                {
                    "name": "Consulting Services",
                    "quantity": "2",
                    "unit_price": "500.00",
                    "discount_type": "PERCENTAGE",
                    "discount_value": "10.00", # 10% disc on 1000 = 900 taxable
                    "tax_rate": "18.00"        # 18% tax on 900 = 162 tax. Total line = 1062
                },
                {
                    "name": "Hardware License",
                    "quantity": "1",
                    "unit_price": "200.00",
                    "discount_type": "FIXED",
                    "discount_value": "50.00", # 50 disc on 200 = 150 taxable
                    "tax_rate": "0.00"         # 0% tax. Total line = 150
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Retrieve document and check assertions
        doc = SalesDocument.objects.get(document_number=response.data['document_number'])
        
        # Subtotal: 1000 + 200 = 1200
        self.assertEqual(doc.subtotal, Decimal('1200.00'))
        
        # Discount: 100 + 50 = 150
        self.assertEqual(doc.discount_amount, Decimal('150.00'))
        
        # Tax: 162 + 0 = 162
        self.assertEqual(doc.tax_amount, Decimal('162.00'))
        
        # Grand Total: (1200 - 150) + 162 + 50 = 1050 + 162 + 50 = 1262
        self.assertEqual(doc.grand_total, Decimal('1262.00'))
        
        # Items check
        items = doc.items.all().order_by('sort_order')
        self.assertEqual(items[0].line_total, Decimal('1062.00'))
        self.assertEqual(items[1].line_total, Decimal('150.00'))

    def test_secure_portal_acceptance(self):
        """
        Verify that a customer can view and accept a proposal via public url token
        without requiring log in credentials.
        """
        doc = SalesDocument.objects.create(
            client=self.client_workspace,
            document_type="PROPOSAL",
            document_number="UWO-PRP-2026-00001",
            customer=self.customer,
            customer_name=self.customer.name,
            customer_email=self.customer.email,
            document_date=timezone.now().date(),
            status="SENT",
            secure_token="token_123_xyz",
            version=1
        )
        
        # View via public GET (No Auth)
        self.client.logout()
        url_view = f"/api/public/sales-documents/{doc.secure_token}/"
        response_view = self.client.get(url_view)
        self.assertEqual(response_view.status_code, status.HTTP_200_OK)
        self.assertEqual(response_view.data['status'], 'SENT')
        
        # Accept via public POST
        url_accept = f"/api/public/sales-documents/{doc.secure_token}/accept/"
        accept_data = {
            "name": "Jane Customer Signature",
            "email": "jane@customer.com",
            "comment": "Excited to get started!"
        }
        response_accept = self.client.post(url_accept, accept_data, format='json')
        self.assertEqual(response_accept.status_code, status.HTTP_200_OK)
        
        # Check database updates
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'ACCEPTED')
        self.assertEqual(doc.accepted_by_name, 'Jane Customer Signature')
        self.assertEqual(doc.accepted_comment, 'Excited to get started!')
        
        # Verify activity log was recorded
        activity = doc.activities.filter(activity_type='ACCEPTED').first()
        self.assertIsNotNone(activity)

    def test_invoice_conversion_and_idempotency(self):
        """
        Verify that an accepted quote can be successfully converted to an invoice,
        and subsequent duplicate conversion attempts are rejected.
        """
        doc = SalesDocument.objects.create(
            client=self.client_workspace,
            document_type="QUOTATION",
            document_number="UWO-QTN-2026-00005",
            customer=self.customer,
            customer_name=self.customer.name,
            customer_email=self.customer.email,
            document_date=timezone.now().date(),
            status="ACCEPTED",
            secure_token="token_qtn_abc",
            grand_total=Decimal('500.00'),
            version=1
        )
        
        item = SalesDocumentItem.objects.create(
            document=doc,
            name="Consulting Hours",
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            line_total=Decimal('500.00')
        )

        # Force authentication back for sales agent
        self.client.force_authenticate(user=self.user)
        
        url_convert = f"/api/sales-documents/{doc.id}/convert_invoice/"
        response_convert = self.client.post(url_convert, {}, format='json')
        
        self.assertEqual(response_convert.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_convert.data['document_type'], 'INVOICE')
        self.assertEqual(response_convert.data['grand_total'], '500.00')
        self.assertEqual(response_convert.data['reference_number'], doc.document_number)
        
        # original quote must mark status as CONVERTED
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'CONVERTED')
        
        # Try converting again (should return bad request 400 with duplicate error info)
        response_duplicate = self.client.post(url_convert, {}, format='json')
        self.assertEqual(response_duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invoice already created', response_duplicate.data['error'])
