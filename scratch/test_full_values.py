import os, sys, django, time
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Client, User, Project, Invoice, SalesDocument, Message, AuditLog
from datetime import timedelta
from django.utils import timezone

t0 = time.time()
print("Starting full .values() benchmark...", flush=True)

now = timezone.now()

clients = list(Client.objects.values(
    'id', 'business_name', 'plan', 'status', 'ai_enabled', 'automation_enabled', 'updated_at', 'created_at',
    'whatsapp_access_token', 'whatsapp_phone_number_id', 'facebook_enabled', 'instagram_enabled',
    'gmail_enabled', 'onedrive_enabled', 'google_calendar_enabled', 'google_sheets_enabled',
    'google_docs_enabled', 'google_slides_enabled', 'zoho_enabled', 'youtube_enabled',
    'google_news_enabled', 'outlook_enabled'
))
print(f"Clients values ({len(clients)}): {time.time() - t0:.3f}s", flush=True)

t1 = time.time()
users = list(User.objects.values(
    'id', 'client_id', 'role', 'status', 'username', 'first_name', 'last_name', 'email', 'last_active_at'
))
print(f"Users values ({len(users)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
projects = list(Project.objects.values(
    'id', 'client_id', 'status', 'deadline', 'progress_percentage'
))
print(f"Projects values ({len(projects)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
invoices = list(Invoice.objects.values(
    'id', 'client_id', 'invoice_number', 'total', 'payment_status', 'payment_method', 'currency_symbol', 'created_at'
))
print(f"Invoices values ({len(invoices)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
sales_docs = list(SalesDocument.objects.values(
    'id', 'client_id', 'document_type', 'document_number', 'status', 'customer_name', 'currency_symbol', 'grand_total', 'created_at'
))
print(f"Sales docs values ({len(sales_docs)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
messages_count = Message.objects.count()
print(f"Messages count ({messages_count}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
recent_msgs = list(Message.objects.values(
    'id', 'client_id', 'sender_user_id', 'sender_name', 'from_address', 'channel', 'body', 'created_at', 'status'
).order_by('-created_at')[:8])
print(f"Recent msgs values ({len(recent_msgs)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
recent_audits = list(AuditLog.objects.values(
    'id', 'client_name', 'admin_name', 'action', 'module', 'after_value', 'created_at'
).order_by('-created_at')[:6])
print(f"Recent audits values ({len(recent_audits)}): {time.time() - t1:.3f}s", flush=True)

t1 = time.time()
recent_logins = list(AuditLog.objects.filter(
    action__in=['LOGIN', 'REGISTER & LOGIN']
).values(
    'id', 'client_name', 'admin_name', 'action', 'ip_address', 'created_at'
).order_by('-created_at')[:10])
print(f"Recent logins values ({len(recent_logins)}): {time.time() - t1:.3f}s", flush=True)

print(f"TOTAL TIME FOR ALL OVERVIEW QUERIES: {time.time() - t0:.3f}s", flush=True)
