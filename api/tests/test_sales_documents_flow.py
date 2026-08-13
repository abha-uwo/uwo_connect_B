import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.utils import timezone
from api.models import Client, User, Contact, SalesDocument, SalesDocumentItem, SalesDocumentActivity
from api.services.pdf_service import SalesDocumentPDFService

def run_sales_document_verification():
    print("==========================================================")
    print("RUNNING QUOTATION & PROPOSAL END-TO-END VERIFICATION TEST")
    print("==========================================================")

    # 1. Get test client
    client, _ = Client.objects.get_or_create(
        business_name="Sales Enterprise Suite",
        defaults={'invoice_prefix': 'QTN-TEST'}
    )
    print(f"[OK] Client Workspace: {client.business_name}")

    import secrets
    # 2. Create Test Quotation
    quote = SalesDocument.objects.create(
        client=client,
        document_type='QUOTATION',
        document_number=f"UWO-QTN-2026-{secrets.randbelow(99999):05d}",
        customer_name='Acme Global Corp',
        customer_email='contact@acme.com',
        customer_phone='+15550199',
        currency='USD',
        currency_symbol='$',
        subtotal=1000.00,
        discount_type='PERCENTAGE',
        discount_value=10.00,
        discount_amount=100.00,
        tax_amount=162.00, # 18% on 900
        grand_total=1062.00,
        status='DRAFT',
        secure_token=secrets.token_urlsafe(32),
        document_date=timezone.now().date(),
        valid_until=timezone.now().date() + timezone.timedelta(days=15)
    )

    # Add Item
    SalesDocumentItem.objects.create(
        document=quote,
        name='Enterprise Software License',
        quantity=1,
        unit_price=1000.00,
        discount_type='PERCENTAGE',
        discount_value=10.00,
        tax_rate=18.00,
        line_total=1062.00
    )
    print(f"  [PASS] Quotation Created: {quote.document_number} | Grand Total: ${quote.grand_total}")

    # Generate Quotation PDF
    pdf_buffer = SalesDocumentPDFService.generate_pdf(quote)
    assert pdf_buffer is not None and len(pdf_buffer.getvalue()) > 0, "Quotation PDF generation failed!"
    print(f"  [PASS] Quotation ReportLab PDF Generated ({len(pdf_buffer.getvalue())} bytes)")

    # 3. Create Test Proposal
    prop = SalesDocument.objects.create(
        client=client,
        document_type='PROPOSAL',
        document_number=f"UWO-PRP-2026-{secrets.randbelow(99999):05d}",
        customer_name='Tech Dynamics Inc',
        customer_email='ceo@techdynamics.io',
        currency='USD',
        currency_symbol='$',
        subtotal=5000.00,
        grand_total=5000.00,
        status='SENT',
        secure_token=secrets.token_urlsafe(32),
        document_date=timezone.now().date(),
        valid_until=timezone.now().date() + timezone.timedelta(days=30),
        proposal_sections=[
            {'title': 'Executive Summary', 'content': 'Full scale digital transformation.'},
            {'title': 'Scope of Work', 'content': 'Custom SaaS development and CRM integration.'},
            {'title': 'Timeline & Milestones', 'content': 'Phase 1: 4 weeks, Phase 2: 6 weeks.'}
        ]
    )
    print(f"  [PASS] Proposal Created with Sections: {prop.document_number} ({len(prop.proposal_sections)} sections)")

    # Generate Proposal PDF
    prop_pdf_buffer = SalesDocumentPDFService.generate_pdf(prop)
    assert prop_pdf_buffer is not None and len(prop_pdf_buffer.getvalue()) > 0, "Proposal PDF generation failed!"
    print(f"  [PASS] Proposal ReportLab PDF Generated ({len(prop_pdf_buffer.getvalue())} bytes)")

    print("\n==========================================================")
    print("ALL QUOTATION & PROPOSAL VERIFICATION TESTS PASSED!")
    print("==========================================================")

if __name__ == '__main__':
    run_sales_document_verification()
