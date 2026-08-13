from pymongo import MongoClient

uri = 'mongodb+srv://admin_db_user:admin%40123@cluster0.drmnlav.mongodb.net/?appName=Cluster0'
client = MongoClient(uri)
db = client['aisaconnect_db_v5']

user = db['api_user'].find_one({'email': 'devanshclg2004@gmail.com'})
if user:
    client_id = user.get('client_id')
    if client_id:
        result = db['api_client'].update_one({'_id': client_id}, {'$unset': {'instagram_config': 1}, '$set': {'instagram_enabled': False}})
        print(f"Modified: {result.modified_count}")
