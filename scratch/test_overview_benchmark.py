import os, sys, django, time
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from datetime import timedelta
from django.utils import timezone
from api.models import (
    Client, User, Message, Conversation, Contact, Product, Order,
    PaymentOrder, ProductPayment, SalesDocument, SalesDocumentItem,
    Invoice, WorkReport, Task, Project, KnowledgeDocument, KnowledgeChunk,
    EmailAccount, EmailMessage, TeamChannel, TeamChatMessage,
    Attendance, LeaveRequest, AuditLog, Automation, Workflow, SupportMessage
)

def benchmark(name, fn):
    t0 = time.time()
    res = fn()
    dur = time.time() - t0
    print(f"[{time.strftime('%H:%M:%S')}] {name}: took {dur:.2f}s", flush=True)
    return res

print("Starting benchmark...", flush=True)
clients = benchmark("Client.objects.all()", lambda: list(Client.objects.all()))
users = benchmark("User.objects.all()", lambda: list(User.objects.all()))
projects = benchmark("Project.objects.all()", lambda: list(Project.objects.all()))
invoices = benchmark("Invoice.objects.all()", lambda: list(Invoice.objects.all()))
sales_docs = benchmark("SalesDocument.objects.all()", lambda: list(SalesDocument.objects.all()))
messages_count = benchmark("Message.objects.count()", lambda: Message.objects.count())

import django.db.models
def safe_sum(queryset, field_name):
    result = queryset.aggregate(total=django.db.models.Sum(field_name))['total']
    return float(result) if result else 0.0

q_val = benchmark("safe_sum quotation", lambda: safe_sum(SalesDocument.objects.filter(document_type='QUOTATION'), 'grand_total'))
p_val = benchmark("safe_sum proposal", lambda: safe_sum(SalesDocument.objects.filter(document_type='PROPOSAL'), 'grand_total'))

users_with_client = benchmark("User.objects.select_related('client')", lambda: list(User.objects.all().select_related('client')))
projects_with_client = benchmark("Project.objects.select_related('client')", lambda: list(Project.objects.all().select_related('client')))
invoices_with_client = benchmark("Invoice.objects.select_related('client')", lambda: list(Invoice.objects.all().select_related('client')))
sales_with_client = benchmark("SalesDocument.objects.select_related('client')", lambda: list(SalesDocument.objects.all().select_related('client')))

recent_msgs = benchmark("Message order_by created_at [:8]", lambda: list(Message.objects.order_by('-created_at')[:8]))
recent_audits = benchmark("AuditLog order_by created_at [:6]", lambda: list(AuditLog.objects.order_by('-created_at')[:6]))
recent_logins = benchmark("AuditLog filter login [:10]", lambda: list(AuditLog.objects.filter(action__in=['LOGIN', 'REGISTER & LOGIN']).order_by('-created_at')[:10]))

print("Done! Total benchmark passed.")
