import os
import logging
import traceback
from django.conf import settings
from django.utils import timezone
from api.models import Invoice, ProductPayment, Order, Contact, Client
from api.services.invoice_pdf_service import InvoicePDFService

logger = logging.getLogger(__name__)

class InvoiceService:
    @staticmethod
    def get_currency_symbol(currency_code):
        return InvoicePDFService.get_currency_symbol(currency_code)

    @staticmethod
    def generate_next_invoice_number(client):
        """Generates sequential invoice number per client: INV-2026-1001."""
        prefix = getattr(client, 'invoice_prefix', 'INV') or 'INV'
        next_num = getattr(client, 'invoice_next_number', 1001) or 1001
        year = timezone.now().year
        
        inv_num = f"{prefix}-{year}-{next_num}"
        
        # Increment next number on client
        try:
            client.invoice_next_number = next_num + 1
            client.save(update_fields=['invoice_next_number'])
        except Exception as e:
            logger.warning(f"Error updating invoice_next_number on client {client.id}: {e}")
            
        return inv_num

    @staticmethod
    def create_invoice_for_payment(payment_record):
        """
        Idempotent invoice creation from a verified ProductPayment or Order.
        Preserves exact transaction currency (USD, INR, EUR, GBP, etc.) and amounts.
        """
        if not payment_record:
            return None

        workspace = getattr(payment_record, 'workspace', None) or getattr(payment_record, 'client', None)
        if not workspace:
            logger.error("Cannot create invoice: Payment record has no associated workspace/client.")
            return None

        payment_id = getattr(payment_record, 'razorpay_payment_id', None) or getattr(payment_record, 'cf_payment_id', None) or str(payment_record.id)
        order_id = getattr(payment_record, 'razorpay_order_id', None) or getattr(payment_record, 'order_id', None) or f"ORD-{payment_record.id}"

        # ── Idempotency Check: check if invoice already exists for this payment_id or order_id
        existing = Invoice.objects.filter(client=workspace).filter(
            payment_id=payment_id
        ).first() if payment_id else None

        if not existing and order_id:
            existing = Invoice.objects.filter(client=workspace).filter(
                order_reference=order_id
            ).first()

        if existing:
            logger.info(f"[InvoiceService] Invoice already exists for payment {payment_id} / order {order_id}: {existing.invoice_number}")
            return existing

        # Extract transaction currency and amounts
        currency = str(getattr(payment_record, 'currency', 'USD') or 'USD').upper()
        currency_symbol = InvoiceService.get_currency_symbol(currency)
        total_amount = float(getattr(payment_record, 'amount', 0) or 0)
        
        # Determine seller & customer details
        seller_details = {
            'company_name': getattr(workspace, 'business_name', 'UWOConnect Partner'),
            'address': getattr(workspace, 'address', ''),
            'phone': getattr(workspace, 'phone_number', ''),
            'email': getattr(workspace, 'email', ''),
            'tax_id_gstin': getattr(workspace, 'tax_id_gstin', ''),
            'logo_url': getattr(workspace, 'company_logo_url', ''),
        }

        cust_name = getattr(payment_record, 'customer_name', '') or 'Valued Customer'
        cust_email = getattr(payment_record, 'customer_email', '') or ''
        cust_phone = getattr(payment_record, 'customer_phone', '') or ''

        # Match contact profile if available
        contact = None
        if cust_phone or cust_email:
            contact = Contact.objects.filter(client=workspace).filter(
                phone_number=cust_phone
            ).first() if cust_phone else None
            if not contact and cust_email:
                contact = Contact.objects.filter(client=workspace).filter(email=cust_email).first()

        billing_details = {
            'name': cust_name,
            'email': cust_email,
            'phone': cust_phone,
            'address': '',
        }

        # Line items
        line_items = []
        product = getattr(payment_record, 'product', None)
        if product:
            line_items.append({
                'product_id': str(product.id),
                'name': product.name,
                'quantity': 1,
                'unit_price': total_amount,
                'tax': 0.00,
                'total': total_amount,
            })
        else:
            line_items.append({
                'product_id': 'CUSTOM',
                'name': 'Order Purchase',
                'quantity': 1,
                'unit_price': total_amount,
                'tax': 0.00,
                'total': total_amount,
            })

        inv_number = InvoiceService.generate_next_invoice_number(workspace)
        payment_status = getattr(payment_record, 'payment_status', 'PAID') or 'PAID'

        invoice = Invoice.objects.create(
            client=workspace,
            invoice_number=inv_number,
            payment_record=payment_record if isinstance(payment_record, ProductPayment) else None,
            contact=contact,
            payment_id=payment_id,
            order_reference=order_id,
            channel=getattr(payment_record, 'channel', 'WEBSITE') or 'WEBSITE',
            currency=currency,
            currency_symbol=currency_symbol,
            subtotal=total_amount,
            discount=0.00,
            shipping=0.00,
            tax=0.00,
            total=total_amount,
            amount_paid=total_amount if payment_status == 'PAID' else 0.00,
            balance_due=0.00 if payment_status == 'PAID' else total_amount,
            payment_status=payment_status,
            invoice_status='PENDING',
            payment_method=getattr(payment_record, 'payment_method', 'Razorpay') or 'Razorpay',
            invoice_date=timezone.now(),
            payment_date=getattr(payment_record, 'paid_at', timezone.now()) or timezone.now(),
            seller_details=seller_details,
            billing_details=billing_details,
            shipping_details=billing_details,
            line_items=line_items,
        )

        # Build PDF file
        InvoiceService.build_pdf_and_save(invoice)
        return invoice

    @staticmethod
    def build_pdf_and_save(invoice):
        """Generates PDF for the invoice and saves file path."""
        try:
            pdf_buffer = InvoicePDFService.generate_pdf(invoice)
            
            # Directory for storing invoice PDFs
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            inv_dir = os.path.join(media_root, 'invoices')
            os.makedirs(inv_dir, exist_ok=True)
            
            filename = f"{invoice.invoice_number.replace('/', '_')}.pdf"
            file_path = os.path.join(inv_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
                
            invoice.pdf_file_path = file_path
            invoice.invoice_status = 'GENERATED'
            invoice.error_log = None
            invoice.save(update_fields=['pdf_file_path', 'invoice_status', 'error_log'])
            logger.info(f"[InvoiceService] PDF generated successfully for {invoice.invoice_number} at {file_path}")
            return True
        except Exception as e:
            logger.error(f"[InvoiceService] Error generating PDF for invoice {invoice.invoice_number}: {e}\n{traceback.format_exc()}")
            invoice.invoice_status = 'FAILED'
            invoice.error_log = str(e)
            invoice.save(update_fields=['invoice_status', 'error_log'])
            return False

    @staticmethod
    def regenerate_invoice(invoice):
        """Regenerates PDF for an existing invoice."""
        return InvoiceService.build_pdf_and_save(invoice)
