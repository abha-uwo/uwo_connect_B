import os, sys, time
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from api.models import Invoice, SalesDocument, Client, User, Project, Message
import pymongo

t0 = time.time()
print("Connecting directly to MongoDB via pymongo...", flush=True)
client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb+srv://admin_db_user:admin%40123@cluster0.drmnlav.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true'))
db = client[os.getenv('MONGODB_DB_NAME', 'aisaconnect_db_v5')]

t1 = time.time()
print(f"Connected in {t1 - t0:.2f}s", flush=True)

# Test pymongo queries
t0 = time.time()
invoices_raw = list(db['api_invoice'].find({}, {'_id': 1, 'client_id': 1, 'invoice_number': 1, 'total': 1, 'payment_status': 1, 'payment_method': 1, 'currency_symbol': 1, 'created_at': 1}))
print(f"pymongo invoices ({len(invoices_raw)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
sales_docs_raw = list(db['api_salesdocument'].find({}, {'_id': 1, 'client_id': 1, 'document_type': 1, 'document_number': 1, 'status': 1, 'customer_name': 1, 'currency_symbol': 1, 'grand_total': 1, 'created_at': 1}))
print(f"pymongo sales docs ({len(sales_docs_raw)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
clients_raw = list(db['api_client'].find({}))
print(f"pymongo clients ({len(clients_raw)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
users_raw = list(db['api_user'].find({}, {'_id': 1, 'client_id': 1, 'role': 1, 'status': 1, 'username': 1, 'first_name': 1, 'last_name': 1, 'email': 1, 'last_active_at': 1}))
print(f"pymongo users ({len(users_raw)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
projects_raw = list(db['api_project'].find({}, {'_id': 1, 'client_id': 1, 'status': 1, 'deadline': 1, 'progress_percentage': 1}))
print(f"pymongo projects ({len(projects_raw)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
messages_count = db['api_message'].count_documents({})
print(f"pymongo message count ({messages_count}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
recent_messages = list(db['api_message'].find({}).sort('created_at', -1).limit(8))
print(f"pymongo recent messages ({len(recent_messages)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
recent_audits = list(db['api_auditlog'].find({}).sort('created_at', -1).limit(6))
print(f"pymongo recent audits ({len(recent_audits)}): {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
recent_logins = list(db['api_auditlog'].find({'action': {'$in': ['LOGIN', 'REGISTER & LOGIN']}}).sort('created_at', -1).limit(10))
print(f"pymongo recent logins ({len(recent_logins)}): {time.time() - t0:.3f}s", flush=True)
