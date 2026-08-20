import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from django.db import connection

db = connection.database

def create_idx(col_name, fields):
    col = db[col_name]
    print(f"Creating index on {col_name} for fields {fields}...")
    name = "_".join(fields) + "_idx"
    res = col.create_index([(f, 1) for f in fields], name=name)
    print(f"Result: {res}")

create_idx("api_invoice", ["client_id"])
create_idx("api_workreport", ["client_id"])
create_idx("api_auditlog", ["client_name"])
create_idx("api_auditlog", ["action"])

print("All indexes created successfully!")
