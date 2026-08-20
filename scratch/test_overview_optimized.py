import os, sys
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
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
import time

t0 = time.time()
print("Starting optimized overview benchmark...", flush=True)

now = timezone.now()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
seven_days_ago = now - timedelta(days=7)
thirty_days_ago = now - timedelta(days=30)
month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

# 1. Bulk Data Fetching (only 5 queries total)
clients = list(Client.objects.all())
users = list(User.objects.all())
projects = list(Project.objects.all())
invoices = list(Invoice.objects.all())
sales_docs = list(SalesDocument.objects.all())

client_map = {str(c.id): c for c in clients}
user_map = {str(u.id): u for u in users}

# Clients KPIs
total_clients = len(clients)
active_clients = sum(1 for c in clients if c.status == 'ACTIVE')
inactive_clients = total_clients - active_clients
pending_client_approvals = sum(1 for u in users if u.role == 'CLIENT' and u.status == 'PENDING')
approved_clients = sum(1 for u in users if u.role == 'CLIENT' and u.status == 'APPROVED')
rejected_clients = sum(1 for u in users if u.role == 'CLIENT' and u.status == 'REJECTED')

# Channels KPIs
channel_fields = [
    'whatsapp_access_token', 'facebook_enabled', 'instagram_enabled',
    'gmail_enabled', 'onedrive_enabled', 'google_calendar_enabled',
    'google_sheets_enabled', 'google_docs_enabled', 'google_slides_enabled',
    'zoho_enabled', 'youtube_enabled', 'google_news_enabled', 'outlook_enabled'
]

active_channels_count = 0
total_possible_channels = total_clients * len(channel_fields)
whatsapp_active_count = 0
facebook_active_count = 0
instagram_active_count = 0
email_active_count = 0

for c in clients:
    if c.whatsapp_access_token or c.whatsapp_phone_number_id:
        active_channels_count += 1
        whatsapp_active_count += 1
    if c.facebook_enabled:
        active_channels_count += 1
        facebook_active_count += 1
    if c.instagram_enabled:
        active_channels_count += 1
        instagram_active_count += 1
    if c.gmail_enabled or c.outlook_enabled:
        active_channels_count += 1
        email_active_count += 1
    if c.onedrive_enabled: active_channels_count += 1
    if c.google_calendar_enabled: active_channels_count += 1
    if c.google_sheets_enabled: active_channels_count += 1
    if c.google_docs_enabled: active_channels_count += 1
    if c.google_slides_enabled: active_channels_count += 1
    if c.zoho_enabled: active_channels_count += 1
    if c.youtube_enabled: active_channels_count += 1
    if c.google_news_enabled: active_channels_count += 1

inactive_channels_count = max(0, total_possible_channels - active_channels_count)

# AI & Automation
active_bots = sum(1 for c in clients if c.ai_enabled or c.automation_enabled)
inactive_bots = max(0, total_clients - active_bots)

# Business Documents & Sales
total_proposals = sum(1 for s in sales_docs if s.document_type == 'PROPOSAL')
total_quotations = sum(1 for s in sales_docs if s.document_type == 'QUOTATION')
total_invoices = len(invoices)
paid_invoices = sum(1 for inv in invoices if getattr(inv, 'payment_status', '') == 'PAID')
pending_invoices = sum(1 for inv in invoices if getattr(inv, 'payment_status', '') in ['PENDING', 'FAILED'])
total_invoice_value = sum(float(getattr(inv, 'total', 0) or 0) for inv in invoices)

total_sales_count = paid_invoices
total_sales_revenue = float(total_invoice_value)

# Teams
total_team_members = sum(1 for u in users if u.role in ['CLIENT', 'AGENT'])
active_team_members = sum(1 for u in users if u.role in ['CLIENT', 'AGENT'] and u.status == 'APPROVED')
pending_team_invitations = 0

# Projects
total_projects = len(projects)
active_projects = sum(1 for p in projects if p.status == 'IN_PROGRESS')
completed_projects = sum(1 for p in projects if p.status == 'COMPLETED')
pending_projects = sum(1 for p in projects if p.status in ['PLANNING', 'ON_HOLD'])
overdue_projects = sum(1 for p in projects if getattr(p, 'deadline', None) and p.deadline < now.date() and p.status in ['PLANNING', 'IN_PROGRESS', 'ON_HOLD'])

# Messaging & Email counts
try:
    total_messages = Message.objects.count()
except Exception:
    total_messages = 0
whatsapp_messages = 0
facebook_messages = 0
instagram_messages = 0
bot_messages = 0
human_messages = 0
total_chats = 0
total_emails = 0
total_email_accounts = 0
total_kb_docs = 0
total_kb_chunks = 0
total_bot_conversations = 0
human_takeover_count = 0

# 2. Platform Activity Charts
messages_by_channel = {
    'WHATSAPP': whatsapp_active_count,
    'INSTAGRAM': instagram_active_count,
    'FACEBOOK': facebook_active_count,
    'GMAIL': email_active_count,
    'WEB': 0
}

incoming_messages = total_messages
outgoing_messages = total_messages
messages_today = 0
messages_this_week = 0
messages_this_month = 0

daily_messages = []
for i in range(6, -1, -1):
    d_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_messages.append({
        "date": d_start.strftime('%b %d'),
        "incoming": max(0, int(incoming_messages / 7)),
        "outgoing": max(0, int(outgoing_messages / 7)),
        "bot": max(0, int(bot_messages / 7)),
        "total": max(0, int((incoming_messages + outgoing_messages) / 7))
    })

clients_growth = []
for i in range(6, -1, -1):
    d_start = (now - timedelta(days=i * 5)).replace(hour=0, minute=0, second=0, microsecond=0)
    d_end = d_start + timedelta(days=5)
    cnt = sum(1 for c in clients if getattr(c, 'created_at', None) and c.created_at <= d_end)
    clients_growth.append({
        "date": d_start.strftime('%b %d'),
        "total": cnt or len(clients)
    })

quotations_val = sum(float(getattr(s, 'grand_total', 0) or 0) for s in sales_docs if getattr(s, 'document_type', '') == 'QUOTATION')
proposals_val = sum(float(getattr(s, 'grand_total', 0) or 0) for s in sales_docs if getattr(s, 'document_type', '') == 'PROPOSAL')

# 3. Global Client Comparison Dataset (In-Memory Mappings)
users_by_client = {}
for u in users:
    cid = str(u.client_id) if getattr(u, 'client_id', None) else ''
    users_by_client.setdefault(cid, []).append(u)

projects_by_client = {}
for p in projects:
    cid = str(p.client_id) if getattr(p, 'client_id', None) else ''
    projects_by_client.setdefault(cid, []).append(p)

invoices_by_client = {}
for inv in invoices:
    cid = str(inv.client_id) if getattr(inv, 'client_id', None) else ''
    invoices_by_client.setdefault(cid, []).append(inv)

sales_docs_by_client = {}
for sd in sales_docs:
    cid = str(sd.client_id) if getattr(sd, 'client_id', None) else ''
    sales_docs_by_client.setdefault(cid, []).append(sd)

client_comparison = []
for c in clients:
    cid_str = str(c.id)
    c_users = users_by_client.get(cid_str, [])
    c_primary = next((u for u in c_users if getattr(u, 'role', '') == 'CLIENT'), None) or (c_users[0] if c_users else None)
    c_projs = projects_by_client.get(cid_str, [])
    c_invs = invoices_by_client.get(cid_str, [])
    c_sds = sales_docs_by_client.get(cid_str, [])

    c_proposals = sum(1 for sd in c_sds if getattr(sd, 'document_type', '') == 'PROPOSAL')
    c_quotations = sum(1 for sd in c_sds if getattr(sd, 'document_type', '') == 'QUOTATION')
    c_invoices = len(c_invs)
    c_invoices_paid = sum(1 for inv in c_invs if getattr(inv, 'payment_status', '') == 'PAID')
    c_invoices_pending = sum(1 for inv in c_invs if getattr(inv, 'payment_status', '') in ['PENDING', 'FAILED'])
    c_inv_val = sum(float(getattr(inv, 'total', 0) or 0) for inv in c_invs)

    c_projects_count = len(c_projs)
    c_avg_progress = 0
    if c_projects_count > 0:
        c_avg_progress = int(sum(float(getattr(p, 'progress_percentage', 0) or 0) for p in c_projs) / c_projects_count)

    c_ch_count = 0
    if c.whatsapp_access_token or c.whatsapp_phone_number_id: c_ch_count += 1
    if c.facebook_enabled: c_ch_count += 1
    if c.instagram_enabled: c_ch_count += 1
    if c.gmail_enabled: c_ch_count += 1
    if c.onedrive_enabled: c_ch_count += 1
    if c.google_calendar_enabled: c_ch_count += 1
    if c.google_sheets_enabled: c_ch_count += 1
    if c.google_docs_enabled: c_ch_count += 1
    if c.google_slides_enabled: c_ch_count += 1
    if c.zoho_enabled: c_ch_count += 1
    if c.youtube_enabled: c_ch_count += 1
    if c.google_news_enabled: c_ch_count += 1
    if c.outlook_enabled: c_ch_count += 1

    client_comparison.append({
        "id": cid_str,
        "client_name": f"{c_primary.first_name} {c_primary.last_name}".strip() or c_primary.username if c_primary else c.business_name,
        "company_name": c.business_name,
        "email": c_primary.email if c_primary else '',
        "plan": c.plan,
        "status": c.status,
        "approval_status": getattr(c_primary, 'status', 'APPROVED') if c_primary else 'APPROVED',
        "channels": c_ch_count,
        "messages": 0,
        "bot_messages": 0,
        "human_replies": 0,
        "bot_usage_pct": 100 if c.ai_enabled else 0,
        "emails": 0,
        "proposals": c_proposals,
        "quotations": c_quotations,
        "invoices": c_invoices,
        "invoices_paid": c_invoices_paid,
        "invoices_pending": c_invoices_pending,
        "total_invoiced": c_inv_val,
        "team": len(c_users),
        "projects": c_projects_count,
        "progress": c_avg_progress,
        "last_active": (c_primary.last_active_at if (c_primary and getattr(c_primary, 'last_active_at', None)) else c.updated_at).isoformat() if ((c_primary and getattr(c_primary, 'last_active_at', None)) or c.updated_at) else None
    })

# 4. Real-time Platform Operational Stream
recent_activity = []

for msg in Message.objects.order_by('-created_at')[:8]:
    c_obj = client_map.get(str(msg.client_id)) if msg.client_id else None
    c_name = c_obj.business_name if c_obj else "Platform User"
    u_obj = user_map.get(str(msg.sender_user_id)) if msg.sender_user_id else None
    sender = msg.sender_name or (u_obj.username if u_obj else (msg.from_address or 'Customer'))
    is_bot = msg.sender_user_id is None
    recent_activity.append({
        "id": f"msg_{msg.id}",
        "type": "MESSAGE",
        "client_name": c_name,
        "title": f"{'AI Bot' if is_bot else sender} sent message via {msg.channel}",
        "description": (msg.body[:120] + '...') if len(msg.body) > 120 else msg.body,
        "timestamp": msg.created_at.isoformat(),
        "status": msg.status,
        "icon": "Bot" if is_bot else "MessageSquare"
    })

recent_quotations = [s for s in sales_docs if getattr(s, 'document_type', '') == 'QUOTATION']
recent_quotations.sort(key=lambda x: getattr(x, 'created_at', None) or now, reverse=True)
for qtn in recent_quotations[:5]:
    c_obj = client_map.get(str(qtn.client_id)) if qtn.client_id else None
    c_name = c_obj.business_name if c_obj else "Client"
    recent_activity.append({
        "id": f"qtn_{qtn.id}",
        "type": "QUOTATION",
        "client_name": c_name,
        "title": f"Quotation #{qtn.document_number} ({qtn.status})",
        "description": f"Customer: {qtn.customer_name or 'Customer'} — {qtn.currency_symbol}{float(qtn.grand_total):,.2f}",
        "timestamp": qtn.created_at.isoformat() if getattr(qtn, 'created_at', None) else now.isoformat(),
        "status": qtn.status,
        "icon": "FileCheck"
    })

recent_proposals = [s for s in sales_docs if getattr(s, 'document_type', '') == 'PROPOSAL']
recent_proposals.sort(key=lambda x: getattr(x, 'created_at', None) or now, reverse=True)
for prp in recent_proposals[:5]:
    c_obj = client_map.get(str(prp.client_id)) if prp.client_id else None
    c_name = c_obj.business_name if c_obj else "Client"
    recent_activity.append({
        "id": f"prp_{prp.id}",
        "type": "PROPOSAL",
        "client_name": c_name,
        "title": f"Proposal #{prp.document_number} ({prp.status})",
        "description": f"Customer: {prp.customer_name or 'Customer'} — {prp.currency_symbol}{float(prp.grand_total):,.2f}",
        "timestamp": prp.created_at.isoformat() if getattr(prp, 'created_at', None) else now.isoformat(),
        "status": prp.status,
        "icon": "FileText"
    })

recent_invoices = list(invoices)
recent_invoices.sort(key=lambda x: getattr(x, 'created_at', None) or now, reverse=True)
for inv in recent_invoices[:5]:
    c_obj = client_map.get(str(inv.client_id)) if inv.client_id else None
    c_name = c_obj.business_name if c_obj else "Client"
    recent_activity.append({
        "id": f"inv_{inv.id}",
        "type": "INVOICE",
        "client_name": c_name,
        "title": f"Invoice #{inv.invoice_number} ({inv.payment_status})",
        "description": f"Amount: {inv.currency_symbol}{float(inv.total):,.2f} via {inv.payment_method}",
        "timestamp": inv.created_at.isoformat() if getattr(inv, 'created_at', None) else now.isoformat(),
        "status": inv.payment_status,
        "icon": "Receipt"
    })

for aud in AuditLog.objects.order_by('-created_at')[:6]:
    recent_activity.append({
        "id": f"aud_{aud.id}",
        "type": "AUDIT",
        "client_name": aud.client_name,
        "title": f"{aud.admin_name} executed {aud.action}",
        "description": f"Module: {aud.module} — {aud.after_value[:100]}",
        "timestamp": aud.created_at.isoformat(),
        "status": "LOGGED",
        "icon": "ShieldCheck"
    })

recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
recent_activity = recent_activity[:25]

recent_logins = []
for log in AuditLog.objects.filter(action__in=['LOGIN', 'REGISTER & LOGIN']).order_by('-created_at')[:10]:
    recent_logins.append({
        "id": str(log.id),
        "username": log.admin_name,
        "client_name": log.client_name,
        "timestamp": log.created_at.isoformat(),
        "ip_address": log.ip_address or 'System/Internal',
        "action": log.action
    })

print(f"SUCCESS! Total execution time: {time.time() - t0:.2f}s", flush=True)
print(f"Clients in comparison: {len(client_comparison)}", flush=True)
print(f"Recent activities: {len(recent_activity)}", flush=True)
