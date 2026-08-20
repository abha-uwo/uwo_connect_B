import os
import django
import sys
import time

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client, User, Message, Conversation, SalesDocument, Invoice, ProductPayment, WorkReport, AuditLog
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta

client_id = '6a5338debec6daea1165d2b3'
client = Client.objects.get(id=client_id)
print("Loaded client.")

now = timezone.now()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
seven_days_ago = now - timedelta(days=7)
month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def benchmark(name, fn):
    t0 = time.time()
    res = fn()
    t1 = time.time()
    print(f"[{name}] took {t1 - t0:.3f}s")
    return res

# Helper
def safe_get_relation_attr(instance, relation_name, attr_name, default=""):
    try:
        rel = getattr(instance, relation_name)
        if rel:
            return getattr(rel, attr_name, default)
    except Exception:
        pass
    return default

# 1. Overview
primary_user = benchmark("Get primary user", lambda: client.users.filter(role='CLIENT').first() or client.users.first())

# 2. Messages
client_msgs = client.messages.all()
client_convos = client.conversations.all()

# WhatsApp drill down (Optimized)
wa_convos = client_convos.filter(channel='WHATSAPP')
def run_wa_drill():
    wa_conversation_list = []
    for convo in wa_convos.order_by('-updated_at')[:25]:
        thread_msgs = list(Message.objects.filter(conversation=convo).order_by('-created_at')[:10])
        last_m = thread_msgs[0] if thread_msgs else None
        recent_thread = []
        for m in thread_msgs:
            recent_thread.append({
                "id": str(m.id),
                "sender": "AI Bot" if m.sender_user is None else (m.sender_name or safe_get_relation_attr(m, 'sender_user', 'username', 'Customer')),
                "is_bot": m.sender_user is None,
                "body": m.body,
                "timestamp": m.created_at.isoformat(),
                "type": m.message_type
            })
        wa_conversation_list.append({
            "id": str(convo.id),
            "customer_name": safe_get_relation_attr(convo, 'contact', 'name', convo.customer_phone or "Customer"),
            "customer_phone": safe_get_relation_attr(convo, 'contact', 'phone_number', convo.customer_phone or "—"),
            "status": convo.status,
            "assigned_to": safe_get_relation_attr(convo, 'assigned_to', 'username', 'Unassigned (Bot)'),
            "unread_count": convo.unread_count_admin + convo.unread_count_employee,
            "last_message": last_m.body if last_m else "",
            "last_message_time": (last_m.created_at if last_m else convo.updated_at).isoformat(),
            "thread": list(reversed(recent_thread))
        })
    return len(wa_conversation_list)

benchmark("WhatsApp drill down (Optimized)", run_wa_drill)

# KB docs
benchmark("KB Docs count", lambda: client.knowledge_docs.count())

# Messages feed (Optimized)
benchmark("Messages feed (Optimized)", lambda: list(client_msgs.only('id', 'created_at', 'sender_user', 'sender_name', 'message_type', 'channel', 'body', 'status').order_by('-created_at')[:40]))

# Email (Optimized)
c_emails = client.email_messages.all()
benchmark("Email activity query (Optimized)", lambda: list(c_emails.only('id', 'created_at', 'sender_email', 'folder', 'status', 'subject').order_by('-created_at')[:30]))

# Proposals (Optimized)
def run_proposals():
    proposals_qs = client.sales_documents.filter(document_type='PROPOSAL').only(
        'id', 'document_number', 'customer_name', 'customer_email', 'customer_company',
        'reference_number', 'grand_total', 'currency_symbol', 'status', 'document_date',
        'valid_until', 'created_at', 'accepted_at', 'secure_token'
    )
    proposals_list = []
    for p in proposals_qs.order_by('-created_at'):
        proposals_list.append(p.id)
    return len(proposals_list)

benchmark("Proposals list (Optimized)", run_proposals)

# Invoices (Optimized)
def run_invoices():
    invoices_qs = client.invoices.all().only(
        'id', 'invoice_number', 'line_items', 'order_reference', 'total', 'currency_symbol',
        'payment_status', 'invoice_status', 'payment_method', 'created_at', 'invoice_date', 'secure_token'
    )
    invoices_list = []
    for inv in invoices_qs.order_by('-created_at'):
        invoices_list.append(inv.id)
    return len(invoices_list)

benchmark("Invoices list (Optimized)", run_invoices)

# Team Management
def run_team():
    team_members_list = []
    for u in client.users.all().order_by('-date_joined'):
        proj_names = [p.name for p in u.assigned_projects.all()]
        msg_cnt = Message.objects.filter(client=client, sender_user=u).count()
        rep_cnt = WorkReport.objects.filter(client=client, employee=u).count()
        team_members_list.append(u.username)
    return len(team_members_list)

benchmark("Team management section", run_team)

# Projects
def run_projects():
    projects_list = []
    c_projects_all = client.projects.all().order_by('-created_at')
    for proj in c_projects_all:
        proj_tasks = proj.tasks.filter(is_archived=False)
        t_total = proj_tasks.count()
        t_done = proj_tasks.filter(status='COMPLETED').count()
        projects_list.append(proj.name)
    return len(projects_list)

benchmark("Projects section", run_projects)

# Activity timeline (Optimized)
def run_timeline():
    activity_timeline = []
    for aud in AuditLog.objects.filter(client_name=client.business_name).only('id', 'created_at', 'admin_name', 'action', 'module', 'after_value').order_by('-created_at')[:20]:
        activity_timeline.append(aud.id)
    for msg in client_msgs.only('id', 'created_at', 'sender_user', 'sender_name', 'message_type', 'channel', 'body', 'status').order_by('-created_at')[:15]:
        activity_timeline.append(msg.id)
    for doc in client.sales_documents.only('id', 'created_at', 'created_by', 'document_type', 'status', 'document_number', 'grand_total', 'currency_symbol', 'customer_name').order_by('-created_at')[:10]:
        activity_timeline.append(doc.id)
    for em in c_emails.only('id', 'created_at', 'sender_email', 'folder', 'status', 'subject').order_by('-created_at')[:10]:
        activity_timeline.append(em.id)
    return len(activity_timeline)

benchmark("Activity timeline section (Optimized)", run_timeline)

print("All optimized done successfully!")
