import os
import django
import sys
import time

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from api.models import Client, User, Message, Conversation, KnowledgeDocument, KnowledgeChunk, SalesDocument, Invoice, ProductPayment, Order, Project, EmailMessage, EmailAccount
from django.utils import timezone
from datetime import timedelta

def measure_time(name, fn):
    t0 = time.time()
    res = fn()
    t1 = time.time()
    print(f"{name}: {t1 - t0:.3f}s (result={res})")

print("Measuring queries...")
measure_time("total_clients", lambda: Client.objects.count())
measure_time("active_clients", lambda: Client.objects.filter(status='ACTIVE').count())
measure_time("pending_client_approvals", lambda: User.objects.filter(role='CLIENT', status='PENDING').count())
measure_time("approved_clients", lambda: User.objects.filter(role='CLIENT', status='APPROVED').count())

# Channels count
clients = list(Client.objects.all())
print(f"Loaded {len(clients)} clients.")

# Messaging
measure_time("total_messages", lambda: Message.objects.count())
measure_time("whatsapp_messages", lambda: Message.objects.filter(channel='WHATSAPP').count())
measure_time("bot_messages", lambda: Message.objects.filter(sender_user__isnull=True).count())
measure_time("human_messages", lambda: Message.objects.filter(sender_user__isnull=False).count())
measure_time("total_chats", lambda: Conversation.objects.count())

# AI
measure_time("active_bots", lambda: Client.objects.filter(ai_enabled=True).count())
measure_time("total_kb_docs", lambda: KnowledgeDocument.objects.count())

# Business Documents
measure_time("total_proposals", lambda: SalesDocument.objects.filter(document_type='PROPOSAL').count())
measure_time("total_invoices", lambda: Invoice.objects.count())

# Teams
measure_time("total_team_members", lambda: User.objects.filter(role__in=['CLIENT', 'AGENT']).count())

# Projects
measure_time("total_projects", lambda: Project.objects.count())

# Emails
measure_time("total_emails", lambda: EmailMessage.objects.count())

# Recent Activity
measure_time("recent_messages", lambda: list(Message.objects.select_related('client', 'sender_user').order_by('-created_at')[:8]))

print("\nDone!")
