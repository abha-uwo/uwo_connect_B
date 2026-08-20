import os, sys
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from datetime import timedelta
from django.utils import timezone
from api.models import (
    Client, User, Message, Project, Invoice, SalesDocument, AuditLog, Product
)
import time

def run_overview():
    t0 = time.time()
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 1. Bulk Data Fetching (5 optimized queries with .values())
    clients = list(Client.objects.values(
        'id', 'business_name', 'plan', 'status', 'ai_enabled', 'automation_enabled', 'updated_at', 'created_at',
        'whatsapp_access_token', 'whatsapp_phone_number_id', 'facebook_enabled', 'instagram_enabled',
        'gmail_enabled', 'onedrive_enabled', 'google_calendar_enabled', 'google_sheets_enabled',
        'google_docs_enabled', 'google_slides_enabled', 'zoho_enabled', 'youtube_enabled',
        'google_news_enabled', 'outlook_enabled'
    ))
    users = list(User.objects.values(
        'id', 'client_id', 'role', 'status', 'username', 'first_name', 'last_name', 'email', 'last_active_at'
    ))
    projects = list(Project.objects.values(
        'id', 'client_id', 'status', 'deadline', 'progress_percentage'
    ))
    invoices = list(Invoice.objects.values(
        'id', 'client_id', 'invoice_number', 'total', 'payment_status', 'payment_method', 'currency_symbol', 'created_at'
    ))
    sales_docs = list(SalesDocument.objects.values(
        'id', 'client_id', 'document_type', 'document_number', 'status', 'customer_name', 'currency_symbol', 'grand_total', 'created_at'
    ))

    # Clients KPIs
    total_clients = len(clients)
    active_clients = sum(1 for c in clients if c.get('status') == 'ACTIVE')
    inactive_clients = total_clients - active_clients
    pending_client_approvals = sum(1 for u in users if u.get('role') == 'CLIENT' and u.get('status') == 'PENDING')
    approved_clients = sum(1 for u in users if u.get('role') == 'CLIENT' and u.get('status') == 'APPROVED')
    rejected_clients = sum(1 for u in users if u.get('role') == 'CLIENT' and u.get('status') == 'REJECTED')

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
        if c.get('whatsapp_access_token') or c.get('whatsapp_phone_number_id'):
            active_channels_count += 1
            whatsapp_active_count += 1
        if c.get('facebook_enabled'):
            active_channels_count += 1
            facebook_active_count += 1
        if c.get('instagram_enabled'):
            active_channels_count += 1
            instagram_active_count += 1
        if c.get('gmail_enabled') or c.get('outlook_enabled'):
            active_channels_count += 1
            email_active_count += 1
        if c.get('onedrive_enabled'): active_channels_count += 1
        if c.get('google_calendar_enabled'): active_channels_count += 1
        if c.get('google_sheets_enabled'): active_channels_count += 1
        if c.get('google_docs_enabled'): active_channels_count += 1
        if c.get('google_slides_enabled'): active_channels_count += 1
        if c.get('zoho_enabled'): active_channels_count += 1
        if c.get('youtube_enabled'): active_channels_count += 1
        if c.get('google_news_enabled'): active_channels_count += 1

    inactive_channels_count = max(0, total_possible_channels - active_channels_count)

    # AI & Automation
    active_bots = sum(1 for c in clients if c.get('ai_enabled') or c.get('automation_enabled'))
    inactive_bots = max(0, total_clients - active_bots)

    # Business Documents & Sales
    total_proposals = sum(1 for s in sales_docs if s.get('document_type') == 'PROPOSAL')
    total_quotations = sum(1 for s in sales_docs if s.get('document_type') == 'QUOTATION')
    total_invoices = len(invoices)
    paid_invoices = sum(1 for inv in invoices if inv.get('payment_status') == 'PAID')
    pending_invoices = sum(1 for inv in invoices if inv.get('payment_status') in ['PENDING', 'FAILED'])
    total_invoice_value = sum(float(inv.get('total', 0) or 0) for inv in invoices)

    total_sales_count = paid_invoices
    total_sales_revenue = float(total_invoice_value)

    # Teams
    total_team_members = sum(1 for u in users if u.get('role') in ['CLIENT', 'AGENT'])
    active_team_members = sum(1 for u in users if u.get('role') in ['CLIENT', 'AGENT'] and u.get('status') == 'APPROVED')
    pending_team_invitations = 0

    # Projects
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.get('status') == 'IN_PROGRESS')
    completed_projects = sum(1 for p in projects if p.get('status') == 'COMPLETED')
    pending_projects = sum(1 for p in projects if p.get('status') in ['PLANNING', 'ON_HOLD'])
    overdue_projects = sum(1 for p in projects if p.get('deadline') and p.get('deadline') < now.date() and p.get('status') in ['PLANNING', 'IN_PROGRESS', 'ON_HOLD'])

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
        cnt = sum(1 for c in clients if c.get('created_at') and c.get('created_at') <= d_end)
        clients_growth.append({
            "date": d_start.strftime('%b %d'),
            "total": cnt or len(clients)
        })

    quotations_val = sum(float(s.get('grand_total', 0) or 0) for s in sales_docs if s.get('document_type') == 'QUOTATION')
    proposals_val = sum(float(s.get('grand_total', 0) or 0) for s in sales_docs if s.get('document_type') == 'PROPOSAL')

    # 3. Global Client Comparison Dataset (In-Memory Mappings)
    client_map = {str(c['id']): c for c in clients}
    user_map = {str(u['id']): u for u in users}

    users_by_client = {}
    for u in users:
        cid = str(u['client_id']) if u.get('client_id') else ''
        users_by_client.setdefault(cid, []).append(u)

    projects_by_client = {}
    for p in projects:
        cid = str(p['client_id']) if p.get('client_id') else ''
        projects_by_client.setdefault(cid, []).append(p)

    invoices_by_client = {}
    for inv in invoices:
        cid = str(inv['client_id']) if inv.get('client_id') else ''
        invoices_by_client.setdefault(cid, []).append(inv)

    sales_docs_by_client = {}
    for sd in sales_docs:
        cid = str(sd['client_id']) if sd.get('client_id') else ''
        sales_docs_by_client.setdefault(cid, []).append(sd)

    client_comparison = []
    for c in clients:
        cid_str = str(c['id'])
        c_users = users_by_client.get(cid_str, [])
        c_primary = next((u for u in c_users if u.get('role') == 'CLIENT'), None) or (c_users[0] if c_users else None)
        c_projs = projects_by_client.get(cid_str, [])
        c_invs = invoices_by_client.get(cid_str, [])
        c_sds = sales_docs_by_client.get(cid_str, [])

        c_proposals = sum(1 for sd in c_sds if sd.get('document_type') == 'PROPOSAL')
        c_quotations = sum(1 for sd in c_sds if sd.get('document_type') == 'QUOTATION')
        c_invoices = len(c_invs)
        c_invoices_paid = sum(1 for inv in c_invs if inv.get('payment_status') == 'PAID')
        c_invoices_pending = sum(1 for inv in c_invs if inv.get('payment_status') in ['PENDING', 'FAILED'])
        c_inv_val = sum(float(inv.get('total', 0) or 0) for inv in c_invs)

        c_projects_count = len(c_projs)
        c_avg_progress = 0
        if c_projects_count > 0:
            c_avg_progress = int(sum(float(p.get('progress_percentage', 0) or 0) for p in c_projs) / c_projects_count)

        c_ch_count = 0
        if c.get('whatsapp_access_token') or c.get('whatsapp_phone_number_id'): c_ch_count += 1
        if c.get('facebook_enabled'): c_ch_count += 1
        if c.get('instagram_enabled'): c_ch_count += 1
        if c.get('gmail_enabled'): c_ch_count += 1
        if c.get('onedrive_enabled'): c_ch_count += 1
        if c.get('google_calendar_enabled'): c_ch_count += 1
        if c.get('google_sheets_enabled'): c_ch_count += 1
        if c.get('google_docs_enabled'): c_ch_count += 1
        if c.get('google_slides_enabled'): c_ch_count += 1
        if c.get('zoho_enabled'): c_ch_count += 1
        if c.get('youtube_enabled'): c_ch_count += 1
        if c.get('google_news_enabled'): c_ch_count += 1
        if c.get('outlook_enabled'): c_ch_count += 1

        client_name = ''
        if c_primary:
            fn = c_primary.get('first_name', '').strip()
            ln = c_primary.get('last_name', '').strip()
            full_name = f"{fn} {ln}".strip()
            client_name = full_name or c_primary.get('username') or c.get('business_name', '')
        else:
            client_name = c.get('business_name', '')

        last_active = None
        if c_primary and c_primary.get('last_active_at'):
            last_active = c_primary['last_active_at'].isoformat()
        elif c.get('updated_at'):
            last_active = c['updated_at'].isoformat()

        client_comparison.append({
            "id": cid_str,
            "client_name": client_name,
            "company_name": c.get('business_name', ''),
            "email": c_primary.get('email', '') if c_primary else '',
            "plan": c.get('plan', ''),
            "status": c.get('status', ''),
            "approval_status": c_primary.get('status', 'APPROVED') if c_primary else 'APPROVED',
            "channels": c_ch_count,
            "messages": 0,
            "bot_messages": 0,
            "human_replies": 0,
            "bot_usage_pct": 100 if c.get('ai_enabled') else 0,
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
            "last_active": last_active
        })

    # 4. Real-time Platform Operational Stream
    recent_activity = []

    for msg in Message.objects.values('id', 'client_id', 'sender_user_id', 'sender_name', 'from_address', 'channel', 'body', 'created_at', 'status').order_by('-created_at')[:8]:
        c_obj = client_map.get(str(msg['client_id'])) if msg.get('client_id') else None
        c_name = c_obj.get('business_name') if c_obj else "Platform User"
        u_obj = user_map.get(str(msg['sender_user_id'])) if msg.get('sender_user_id') else None
        sender = msg.get('sender_name') or (u_obj.get('username') if u_obj else (msg.get('from_address') or 'Customer'))
        is_bot = msg.get('sender_user_id') is None
        body_text = msg.get('body', '') or ''
        recent_activity.append({
            "id": f"msg_{msg['id']}",
            "type": "MESSAGE",
            "client_name": c_name,
            "title": f"{'AI Bot' if is_bot else sender} sent message via {msg.get('channel')}",
            "description": (body_text[:120] + '...') if len(body_text) > 120 else body_text,
            "timestamp": msg['created_at'].isoformat() if msg.get('created_at') else now.isoformat(),
            "status": msg.get('status', ''),
            "icon": "Bot" if is_bot else "MessageSquare"
        })

    recent_quotations = [s for s in sales_docs if s.get('document_type') == 'QUOTATION']
    recent_quotations.sort(key=lambda x: x.get('created_at') or now, reverse=True)
    for qtn in recent_quotations[:5]:
        c_obj = client_map.get(str(qtn['client_id'])) if qtn.get('client_id') else None
        c_name = c_obj.get('business_name') if c_obj else "Client"
        recent_activity.append({
            "id": f"qtn_{qtn['id']}",
            "type": "QUOTATION",
            "client_name": c_name,
            "title": f"Quotation #{qtn.get('document_number')} ({qtn.get('status')})",
            "description": f"Customer: {qtn.get('customer_name') or 'Customer'} — {qtn.get('currency_symbol', '₹')}{float(qtn.get('grand_total', 0) or 0):,.2f}",
            "timestamp": qtn['created_at'].isoformat() if qtn.get('created_at') else now.isoformat(),
            "status": qtn.get('status', ''),
            "icon": "FileCheck"
        })

    recent_proposals = [s for s in sales_docs if s.get('document_type') == 'PROPOSAL']
    recent_proposals.sort(key=lambda x: x.get('created_at') or now, reverse=True)
    for prp in recent_proposals[:5]:
        c_obj = client_map.get(str(prp['client_id'])) if prp.get('client_id') else None
        c_name = c_obj.get('business_name') if c_obj else "Client"
        recent_activity.append({
            "id": f"prp_{prp['id']}",
            "type": "PROPOSAL",
            "client_name": c_name,
            "title": f"Proposal #{prp.get('document_number')} ({prp.get('status')})",
            "description": f"Customer: {prp.get('customer_name') or 'Customer'} — {prp.get('currency_symbol', '₹')}{float(prp.get('grand_total', 0) or 0):,.2f}",
            "timestamp": prp['created_at'].isoformat() if prp.get('created_at') else now.isoformat(),
            "status": prp.get('status', ''),
            "icon": "FileText"
        })

    recent_invoices = list(invoices)
    recent_invoices.sort(key=lambda x: x.get('created_at') or now, reverse=True)
    for inv in recent_invoices[:5]:
        c_obj = client_map.get(str(inv['client_id'])) if inv.get('client_id') else None
        c_name = c_obj.get('business_name') if c_obj else "Client"
        recent_activity.append({
            "id": f"inv_{inv['id']}",
            "type": "INVOICE",
            "client_name": c_name,
            "title": f"Invoice #{inv.get('invoice_number')} ({inv.get('payment_status')})",
            "description": f"Amount: {inv.get('currency_symbol', '₹')}{float(inv.get('total', 0) or 0):,.2f} via {inv.get('payment_method', 'Razorpay')}",
            "timestamp": inv['created_at'].isoformat() if inv.get('created_at') else now.isoformat(),
            "status": inv.get('payment_status', ''),
            "icon": "Receipt"
        })

    for aud in AuditLog.objects.values('id', 'client_name', 'admin_name', 'action', 'module', 'after_value', 'created_at').order_by('-created_at')[:6]:
        after_val = aud.get('after_value', '') or ''
        recent_activity.append({
            "id": f"aud_{aud['id']}",
            "type": "AUDIT",
            "client_name": aud.get('client_name', ''),
            "title": f"{aud.get('admin_name', '')} executed {aud.get('action', '')}",
            "description": f"Module: {aud.get('module', '')} — {after_val[:100]}",
            "timestamp": aud['created_at'].isoformat() if aud.get('created_at') else now.isoformat(),
            "status": "LOGGED",
            "icon": "ShieldCheck"
        })

    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:25]

    recent_logins = []
    for log in AuditLog.objects.filter(action__in=['LOGIN', 'REGISTER & LOGIN']).values('id', 'admin_name', 'client_name', 'created_at', 'ip_address', 'action').order_by('-created_at')[:10]:
        recent_logins.append({
            "id": str(log['id']),
            "username": log.get('admin_name', ''),
            "client_name": log.get('client_name', ''),
            "timestamp": log['created_at'].isoformat() if log.get('created_at') else now.isoformat(),
            "ip_address": log.get('ip_address') or 'System/Internal',
            "action": log.get('action', '')
        })

    result = {
        "kpis": {
            "totalClients": total_clients,
            "activeClients": active_clients,
            "inactiveClients": inactive_clients,
            "pendingClientApprovals": pending_client_approvals,
            "approvedClients": approved_clients,
            "rejectedClients": rejected_clients,
            "totalChannels": total_possible_channels,
            "activeChannels": active_channels_count,
            "inactiveChannels": inactive_channels_count,
            "whatsappChannels": whatsapp_active_count,
            "facebookChannels": facebook_active_count,
            "instagramChannels": instagram_active_count,
            "emailChannels": email_active_count,
            "totalMessages": total_messages,
            "whatsappMessages": whatsapp_messages,
            "facebookMessages": facebook_messages,
            "instagramMessages": instagram_messages,
            "botMessages": bot_messages,
            "humanMessages": human_messages,
            "totalChats": total_chats,
            "activeBots": active_bots,
            "inactiveBots": inactive_bots,
            "totalBotConversations": total_bot_conversations,
            "humanTakeoverCount": human_takeover_count,
            "totalKnowledgeBaseDocuments": total_kb_docs,
            "totalKnowledgeBaseChunks": total_kb_chunks,
            "totalProposals": total_proposals,
            "totalQuotations": total_quotations,
            "totalInvoices": total_invoices,
            "paidInvoices": paid_invoices,
            "pendingInvoices": pending_invoices,
            "totalInvoiceValue": total_invoice_value,
            "totalProducts": Product.objects.count(),
            "totalSales": total_sales_count,
            "totalSalesRevenue": total_sales_revenue,
            "totalTeamMembers": total_team_members,
            "activeTeamMembers": active_team_members,
            "pendingTeamInvitations": pending_team_invitations,
            "totalProjects": total_projects,
            "activeProjects": active_projects,
            "completedProjects": completed_projects,
            "pendingProjects": pending_projects,
            "overdueProjects": overdue_projects,
            "totalEmails": total_emails,
            "totalEmailAccounts": total_email_accounts
        },
        "charts": {
            "messagesToday": messages_today,
            "messagesThisWeek": messages_this_week,
            "messagesThisMonth": messages_this_month,
            "incomingMessages": incoming_messages,
            "outgoingMessages": outgoing_messages,
            "botMessages": bot_messages,
            "humanMessages": human_messages,
            "messagesByChannel": messages_by_channel,
            "dailyMessagesTrend": daily_messages,
            "clientsGrowth": clients_growth,
            "financialDistribution": {
                "quotationsValue": quotations_val,
                "proposalsValue": proposals_val,
                "invoicesValue": total_invoice_value,
                "salesRevenue": total_sales_revenue
            }
        },
        "clientComparison": client_comparison,
        "recentActivity": recent_activity,
        "recentLogins": recent_logins
    }
    print(f"Overview done in {time.time() - t0:.3f}s. Client count: {len(client_comparison)}", flush=True)
    return result

run_overview()
