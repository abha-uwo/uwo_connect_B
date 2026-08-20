import os
import django
import sys
import time

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client, User, Message, Conversation, SalesDocument, Invoice, ProductPayment, WorkReport
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

# 1. Overview
primary_user = benchmark("Get primary user", lambda: client.users.filter(role='CLIENT').first() or client.users.first())

# 2. Messages
client_msgs = client.messages.all()
client_convos = client.conversations.all()
benchmark("Count client msgs", lambda: client_msgs.count())
benchmark("Count msgs sent", lambda: client_msgs.filter(message_type='OUTGOING').count())

# WhatsApp drill down
wa_convos = client_convos.filter(channel='WHATSAPP')
def run_wa_drill():
    wa_conversation_list = []
    for convo in wa_convos.order_by('-updated_at')[:25]:
        thread_msgs = list(Message.objects.filter(conversation=convo).order_by('-created_at')[:10])
        last_m = thread_msgs[0] if thread_msgs else None
        recent_thread = []
        for m in thread_msgs:
            recent_thread.append(str(m.id))
        wa_conversation_list.append({
            "id": str(convo.id),
            "thread_len": len(recent_thread)
        })
    return len(wa_conversation_list)

benchmark("WhatsApp drill down", run_wa_drill)

# KB docs
benchmark("KB Docs count", lambda: client.knowledge_docs.count())

# Messages feed
benchmark("Messages feed", lambda: list(client_msgs.order_by('-created_at')[:40]))

# Email
c_emails = client.email_messages.all()
benchmark("Email activity query", lambda: list(c_emails.order_by('-created_at')[:30]))

# Proposals
proposals_qs = client.sales_documents.filter(document_type='PROPOSAL')
benchmark("Proposals list", lambda: list(proposals_qs.order_by('-created_at')))

# Invoices
invoices_qs = client.invoices.all()
invoices_list = list(invoices_qs.order_by('-created_at'))
print(f"Loaded {len(invoices_list)} invoices.")

# Product wise aggregation
def run_prod_agg():
    product_wise_invoices = []
    for prd in client.products.all():
        matched_invoices = [inv for inv in invoices_list if prd.name.lower() in (inv.line_items[0].get('name', 'Service Item').lower() if inv.line_items else '')]
        p_payments = ProductPayment.objects.filter(workspace=client, product=prd)
        product_wise_invoices.append(prd.name)
    return len(product_wise_invoices)

benchmark("Product wise aggregation", run_prod_agg)

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

# Activity timeline
def run_timeline():
    activity_timeline = []
    for doc in client.sales_documents.order_by('-created_at')[:10]:
        activity_timeline.append(doc.id)
    return len(activity_timeline)

benchmark("Activity timeline section", run_timeline)

print("All done successfully!")
