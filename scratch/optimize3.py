import re

with open('api/views/super_admin_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Email Block
email_old = """        c_emails = client.email_messages.all()
        emails_received = c_emails.filter(folder='inbox').count()
        emails_sent = c_emails.filter(folder='sent').count()
        emails_drafts = c_emails.filter(folder='drafts').count()
        emails_failed = c_emails.filter(status='failed').count()"""

email_new = """        c_emails = client.email_messages.all()
        email_stats = c_emails.aggregate(
            emails_received=Count('id', filter=Q(folder='inbox')),
            emails_sent=Count('id', filter=Q(folder='sent')),
            emails_drafts=Count('id', filter=Q(folder='drafts')),
            emails_failed=Count('id', filter=Q(status='failed')),
        )
        emails_received = email_stats['emails_received']
        emails_sent = email_stats['emails_sent']
        emails_drafts = email_stats['emails_drafts']
        emails_failed = email_stats['emails_failed']"""

content = content.replace(email_old, email_new)

products_old = """        # ── 13. Products & Sales Analytics (Section 14) ─────────────────────────
        products_list = []
        for prd in client.products.all().order_by('-created_at'):
            p_payments = ProductPayment.objects.filter(workspace=client, product=prd, payment_status='PAID')
            p_revenue = safe_sum(p_payments, 'amount')
            p_units = p_payments.count()
            p_inv_cnt = sum(1 for inv in invoices_list if prd.name.lower() in inv['product_name'].lower())
            p_qtn_cnt = quotations_qs.filter(Q(reference_number__icontains=prd.name) | Q(items__product=prd)).distinct().count()
            p_prp_cnt = proposals_qs.filter(Q(reference_number__icontains=prd.name) | Q(items__product=prd)).distinct().count()"""

products_new = """        # ── 13. Products & Sales Analytics (Section 14) ─────────────────────────
        products_list = []
        products_annotated = client.products.annotate(
            p_units_ann=Count('payments', filter=Q(payments__payment_status='PAID')),
            p_revenue_ann=Sum('payments__amount', filter=Q(payments__payment_status='PAID'))
        ).order_by('-created_at')
        
        for prd in products_annotated:
            p_revenue = float(prd.p_revenue_ann or 0.0)
            p_units = prd.p_units_ann or 0
            p_inv_cnt = sum(1 for inv in invoices_list if prd.name.lower() in inv['product_name'].lower())
            
            # Minor queries still, but avoided the ProductPayment ones
            p_qtn_cnt = quotations_qs.filter(Q(reference_number__icontains=prd.name) | Q(items__product=prd)).distinct().count()
            p_prp_cnt = proposals_qs.filter(Q(reference_number__icontains=prd.name) | Q(items__product=prd)).distinct().count()"""

content = content.replace(products_old, products_new)

with open('api/views/super_admin_views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Optimization pass 3 completed.")
