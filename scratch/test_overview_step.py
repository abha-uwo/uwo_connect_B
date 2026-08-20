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

def step(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

step("Starting step test...")

now = timezone.now()

step("Fetching clients...")
clients = list(Client.objects.all())
step(f"Fetched {len(clients)} clients")

step("Fetching users...")
users = list(User.objects.all())
step(f"Fetched {len(users)} users")

step("Fetching projects...")
projects = list(Project.objects.all())
step(f"Fetched {len(projects)} projects")

step("Fetching invoices...")
invoices = list(Invoice.objects.all())
step(f"Fetched {len(invoices)} invoices")

step("Fetching sales_docs...")
sales_docs = list(SalesDocument.objects.all())
step(f"Fetched {len(sales_docs)} sales_docs")

step("Querying Message count...")
total_messages = Message.objects.count()
step(f"Total messages: {total_messages}")

step("Querying safe_sum sales docs...")
import django.db.models
def safe_sum(queryset, field_name):
    result = queryset.aggregate(total=django.db.models.Sum(field_name))['total']
    return float(result) if result else 0.0

q_val = safe_sum(SalesDocument.objects.filter(document_type='QUOTATION'), 'grand_total')
step(f"Quotations val: {q_val}")

p_val = safe_sum(SalesDocument.objects.filter(document_type='PROPOSAL'), 'grand_total')
step(f"Proposals val: {p_val}")

step("Querying select_related users...")
try:
    all_users = list(User.objects.all().select_related('client'))
    step(f"Users with client: {len(all_users)}")
except Exception as e:
    step(f"Error on all_users: {e}")

step("Querying select_related projects...")
try:
    all_projects = list(Project.objects.all().select_related('client'))
    step(f"Projects with client: {len(all_projects)}")
except Exception as e:
    step(f"Error on all_projects: {e}")

step("Querying select_related invoices...")
try:
    all_invoices = list(Invoice.objects.all().select_related('client'))
    step(f"Invoices with client: {len(all_invoices)}")
except Exception as e:
    step(f"Error on all_invoices: {e}")

step("Querying select_related sales_docs...")
try:
    all_sales_docs = list(SalesDocument.objects.all().select_related('client'))
    step(f"Sales docs with client: {len(all_sales_docs)}")
except Exception as e:
    step(f"Error on all_sales_docs: {e}")

step("Querying Message recent activity...")
try:
    msgs = list(Message.objects.order_by('-created_at')[:8])
    step(f"Recent messages: {len(msgs)}")
    for m in msgs:
        step(f"Message {m.id} client: {m.client}")
except Exception as e:
    step(f"Error on recent messages: {e}")

step("Querying AuditLog recent activity...")
try:
    audits = list(AuditLog.objects.order_by('-created_at')[:6])
    step(f"Recent audits: {len(audits)}")
except Exception as e:
    step(f"Error on recent audits: {e}")

step("All steps completed successfully!")
