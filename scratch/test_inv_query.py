import os, sys, django, time
sys.path.insert(0, 'c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import Invoice, SalesDocument
import pymongo

client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME', 'aisaconnect_db_v5')]

def test(name, fn):
    t0 = time.time()
    res = fn()
    print(f"{name}: took {time.time() - t0:.2f}s", flush=True)

test("pymongo invoice find", lambda: list(db['api_invoice'].find()))
test("pymongo salesdocument find", lambda: list(db['api_salesdocument'].find()))
test("Invoice.objects.all().values('id', 'client_id', 'total', 'payment_status')", lambda: list(Invoice.objects.all().values('id', 'client_id', 'total', 'payment_status')))
test("Invoice.objects.all() un-ordered", lambda: list(Invoice.objects.order_by().all()))
test("Invoice.objects.all() default", lambda: list(Invoice.objects.all()))
