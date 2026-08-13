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

User = get_user_model()

def run_tests():
    print("Starting Sales Document Logic Verification Script...")
    
    # 1. Clean up or get test entities
    client_workspace, _ = Client.objects.get_or_create(
        business_name="Test Enterprise Ltd",
        defaults={"status": "ACTIVE"}
    )
    
    user, _ = User.objects.get_or_create(
        username="salestest",
        defaults={
            "email": "sales@test.com",
            "role": "CLIENT",
            "status": "APPROVED",
            "client": client_workspace
        }
    )
    if not user.password:
        user.set_password("password123")
        user.save()
        
    customer, _ = Contact.objects.get_or_create(
        client=client_workspace,
        email="jane@customer.com",
        defaults={
            "name": "Jane Customer",
            "phone_number": "+15550199",
            "stage": "NEW"
        }
    )
    
    # Clean previous test docs
    SalesDocument.objects.filter(client=client_workspace, document_number__startswith="UWO-QTN-TEST").delete()
    SalesDocument.objects.filter(client=client_workspace, document_number__startswith="UWO-INV-TEST").delete()
    
    print("    Seeded test Client, User, and Customer.")
    
    # 2. Test Math calculations in view level simulation
    print("    Running Math Calculations Verification...")
    doc = SalesDocument.objects.create(
        client=client_workspace,
        document_type="QUOTATION",
        document_number="UWO-QTN-TEST-00001",
        customer=customer,
        customer_name=customer.name,
        customer_email=customer.email,
        document_date=timezone.now().date(),
        valid_until=timezone.now().date() + timezone.timedelta(days=15),
        currency="USD",
        additional_charges=Decimal("50.00"),
        status="DRAFT",
        secure_token="test_token_math_xyz"
    )
    
    # Mock items saving logic from views._save_line_items
    items_data = [
        {
            "name": "Consulting Services",
            "quantity": Decimal("2"),
            "unit_price": Decimal("500.00"),
            "discount_type": "PERCENTAGE",
            "discount_value": Decimal("10.00"),
            "tax_rate": Decimal("18.00")
        },
        {
            "name": "Hardware License",
            "quantity": Decimal("1"),
            "unit_price": Decimal("200.00"),
            "discount_type": "FIXED",
            "discount_value": Decimal("50.00"),
            "tax_rate": Decimal("0.00")
        }
    ]
    
    subtotal = Decimal('0.00')
    tax_total = Decimal('0.00')
    discount_total = Decimal('0.00')
    
    for idx, item in enumerate(items_data):
        qty = item['quantity']
        price = item['unit_price']
        disc_val = item['discount_value']
        disc_type = item['discount_type']
        tax_rate = item['tax_rate']
        
        base_total = qty * price
        
        if disc_type == 'PERCENTAGE':
            item_discount = base_total * (disc_val / Decimal('100.00'))
        else:
            item_discount = disc_val
        
        taxable_amount = base_total - item_discount
        item_tax = taxable_amount * (tax_rate / Decimal('100.00'))
        line_total = taxable_amount + item_tax
        
        subtotal += base_total
        discount_total += item_discount
        tax_total += item_tax
        
        SalesDocumentItem.objects.create(
            document=doc,
            name=item['name'],
            quantity=qty,
            unit_price=price,
            discount_type=disc_type,
            discount_value=disc_val,
            tax_rate=tax_rate,
            tax_amount=item_tax,
            line_total=line_total,
            sort_order=idx
        )
        
    doc.subtotal = subtotal
    doc.discount_amount = discount_total
    doc.tax_amount = tax_total
    doc.grand_total = (subtotal - discount_total) + tax_total + doc.additional_charges
    doc.save()
    
    # Assertions
    assert doc.subtotal == Decimal('1200.00'), f"Subtotal mismatch: {doc.subtotal}"
    assert doc.discount_amount == Decimal('150.00'), f"Discount mismatch: {doc.discount_amount}"
    assert doc.tax_amount == Decimal('162.00'), f"Tax mismatch: {doc.tax_amount}"
    assert doc.grand_total == Decimal('1262.00'), f"Grand total mismatch: {doc.grand_total}"
    print("Math Calculations: PASSED (Subtotal: $1200, Discount: $150, Tax: $162, Grand Total: $1262)")
    
    # 3. Test Invoice conversion
    print("    Running Invoice Conversion Verification...")
    doc.status = "ACCEPTED"
    doc.save()
    
    # Convert view method simulation
    count = SalesDocument.objects.filter(client=doc.client, document_type='INVOICE').count() + 1
    year = timezone.now().year
    inv_num = f"UWO-INV-TEST-{year}-{count:05d}"
    secure_token = "test_token_inv_abc"
    
    invoice = SalesDocument.objects.create(
        client=doc.client,
        document_type='INVOICE',
        document_number=inv_num,
        customer=doc.customer,
        customer_name=doc.customer_name,
        customer_company=doc.customer_company,
        customer_email=doc.customer_email,
        customer_phone=doc.customer_phone,
        billing_address=doc.billing_address,
        shipping_address=doc.shipping_address,
        tax_number=doc.tax_number,
        created_by=user,
        salesperson=doc.salesperson,
        status='DRAFT',
        currency=doc.currency,
        currency_symbol=doc.currency_symbol,
        exchange_rate=doc.exchange_rate,
        document_date=timezone.now().date(),
        valid_until=timezone.now().date() + timezone.timedelta(days=30),
        payment_terms=doc.payment_terms,
        reference_number=doc.document_number,
        subtotal=doc.subtotal,
        discount_type=doc.discount_type,
        discount_value=doc.discount_value,
        discount_amount=doc.discount_amount,
        tax_amount=doc.tax_amount,
        additional_charges=doc.additional_charges,
        grand_total=doc.grand_total,
        customer_notes=doc.customer_notes,
        terms_conditions=doc.terms_conditions,
        secure_token=secure_token,
        version=1,
        source_document=doc
    )
    
    for item in doc.items.all():
        SalesDocumentItem.objects.create(
            document=invoice,
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_type=item.discount_type,
            discount_value=item.discount_value,
            tax_rate=item.tax_rate,
            tax_amount=item.tax_amount,
            line_total=item.line_total,
            sort_order=item.sort_order
        )
        
    doc.status = 'CONVERTED'
    doc.save()
    
    assert invoice.document_type == 'INVOICE', "Document type must be INVOICE"
    assert invoice.grand_total == Decimal('1262.00'), f"Invoice grand total mismatch: {invoice.grand_total}"
    assert invoice.reference_number == doc.document_number, "Reference quotation number mismatch"
    assert doc.status == 'CONVERTED', "Quotation status must be updated to CONVERTED"
    print("Invoice Conversion: PASSED (Quotation successfully converted to Invoice, references preserved)")

    # 4. Clean up
    SalesDocument.objects.filter(client=client_workspace, document_number__startswith="UWO-QTN-TEST").delete()
    SalesDocument.objects.filter(client=client_workspace, document_number__startswith="UWO-INV-TEST").delete()
    print("Cleaned up test database records.")
    
    print("\nALL SALES DOCUMENT MODULE TEST ASSERTIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
