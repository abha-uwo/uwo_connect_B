import time
import pymongo
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / 'Desktop' / 'uwoconnect' / 'UWO_CONNECT_B'
env_path = BASE_DIR / '.env'
load_dotenv(env_path, override=True)

db_uri = os.getenv('MONGODB_URI', 'mongodb+srv://admin_db_user:admin%40123@cluster0.drmnlav.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true')
db_name = os.getenv('MONGODB_DB_NAME', 'aisaconnect_db_v5')

print(f"Connecting to MongoDB database: {db_name}")

t0 = time.time()
client = pymongo.MongoClient(db_uri, serverSelectionTimeoutMS=5000)
# Force connection/ping
try:
    client.admin.command('ping')
    ping_time = (time.time() - t0) * 1000
    print(f"Ping successful in {ping_time:.2f} ms")
except Exception as e:
    print(f"Ping failed: {e}")
    exit(1)

db = client[db_name]

# Test collection find times
for col_name in ['api_contact', 'api_client', 'api_message']:
    t_start = time.time()
    try:
        count = db[col_name].count_documents({})
        duration = (time.time() - t_start) * 1000
        print(f"Counted {count} docs in {col_name} in {duration:.2f} ms")
    except Exception as e:
        print(f"Error reading {col_name}: {e}")

    t_start = time.time()
    try:
        docs = list(db[col_name].find().sort('_id', -1).limit(5))
        duration = (time.time() - t_start) * 1000
        print(f"Fetched 5 docs from {col_name} in {duration:.2f} ms")
    except Exception as e:
        print(f"Error fetching from {col_name}: {e}")
