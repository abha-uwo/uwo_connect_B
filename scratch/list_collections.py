import os
import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('c:/Users/USER/Desktop/uwoconnect/uwoconnectforRB')
django.setup()

from django.db import connection

db = connection.database
print("Collections:")
for col_name in db.list_collection_names():
    col = db[col_name]
    indexes = list(col.list_indexes())
    print(f"\nCollection: {col_name} (documents count: {col.count_documents({})})")
    print("Indexes:")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['key']}")
