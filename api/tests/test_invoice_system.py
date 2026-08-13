import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.utils import timezone
from api.models import Client, Product, ProductPayment, Invoice, Contact
from api.services.invoice_service import InvoiceService
from api.services.invoice_pdf_service import InvoicePDFService

def run_invoice_verification():
    print("==========================================================")
    print("RUNNING AUTOMATED INVOICE SYSTEM VERIFICATION SUITE")
    print("==========================================================")

    # 1. Get or create test workspace
    client, _ = Client.objects.get_or_create(
        business_name="Test Enterprise Workspace",
        defaults={
            'invoice_prefix': 'TEST-INV',
            'company_logo_url': '',
            'tax_id_gstin': '29ABCDE1234F1ZH',
            'invoice_default_notes': 'Test invoice default notes.',
            'payment_terms': 'Payment due within 30 days.'
        }
    )
    print(f"[OK] Client Workspace: {client.business_name} (ID: {client.id})")

    # 2. Test Multi-Currency Payments & Invoice Generation (USD, EUR, GBP, INR)
    test_cases = [
        {'currency': 'USD', 'symbol': '$', 'amount': 199.99, 'cust': 'Alice Smith', 'email': 'alice@example.com'},
        {'currency': 'EUR', 'symbol': 'EUR ', 'amount': 149.50, 'cust': 'Bob Mueller', 'email': 'bob@example.de'},
        {'currency': 'GBP', 'symbol': 'GBP ', 'amount': 120.00, 'cust': 'Charlie Brown', 'email': 'charlie@example.co.uk'},
        {'currency': 'INR', 'symbol': 'INR ', 'amount': 9999.00, 'cust': 'Devansh Sharma', 'email': 'devansh@example.in'},
    ]

    generated_invoices = []

    for idx, tc in enumerate(test_cases, start=1):
        pay_id = f"pay_test_{tc['currency']}_{idx}"
        ord_id = f"ord_test_{tc['currency']}_{idx}"

        # Create dummy ProductPayment
        payment = ProductPayment.objects.create(
            workspace=client,
            razorpay_order_id=ord_id,
            razorpay_payment_id=pay_id,
            amount=tc['amount'],
            currency=tc['currency'],
            payment_status='PAID',
            payment_method='Card',
            customer_name=tc['cust'],
            customer_email=tc['email'],
            customer_phone='+15550192834',
            paid_at=timezone.now()
        )

        # Trigger Invoice Service
        invoice = InvoiceService.create_invoice_for_payment(payment)
        assert invoice is not None, f"Invoice creation failed for {tc['currency']}"
        assert invoice.currency == tc['currency'], f"Currency mismatch: expected {tc['currency']}, got {invoice.currency}"
        assert float(invoice.total) == tc['amount'], f"Amount mismatch for {tc['currency']}"
        assert os.path.exists(invoice.pdf_file_path), f"PDF file does not exist at {invoice.pdf_file_path}"
        
        generated_invoices.append(invoice)
        print(f"  [PASS] [{tc['currency']}] Invoice {invoice.invoice_number}: Total = {tc['symbol']}{invoice.total:,.2f} | Status = {invoice.payment_status} | PDF = {os.path.basename(invoice.pdf_file_path)}")

    # 3. Test Idempotency (duplicate creation prevention)
    print("\n[INFO] Testing Webhook Idempotency (Duplicate Prevention)...")
    duplicate_inv = InvoiceService.create_invoice_for_payment(ProductPayment.objects.filter(razorpay_payment_id="pay_test_USD_1").first())
    assert duplicate_inv.id == generated_invoices[0].id, "Idempotency check failed: Duplicate invoice created!"
    print(f"  [PASS] Idempotency verified: Re-triggering payment returns existing invoice #{duplicate_inv.invoice_number}")

    # 4. Test PDF Regeneration
    print("\n[INFO] Testing PDF Regeneration...")
    rebuilt = InvoiceService.regenerate_invoice(generated_invoices[0])
    assert rebuilt is True, "Regeneration failed!"
    assert os.path.exists(generated_invoices[0].pdf_file_path), "Regenerated PDF missing!"
    print(f"  [PASS] PDF Regeneration verified for invoice #{generated_invoices[0].invoice_number}")

    print("\n==========================================================")
    print("ALL INVOICE SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==========================================================")

if __name__ == '__main__':
    run_invoice_verification()
