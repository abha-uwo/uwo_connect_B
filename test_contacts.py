import urllib.request
import sys

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MjA3MTY5LCJpYXQiOjE3ODcxMjA3NzksImp0aSI6IjUyNjZhOTBmN2UzZjQ0NDVhYmUyYTIwYzQxNTIzOTE1IiwidXNlcl9pZCI6IjZhNzcxNDZiNjg4NWU5ODlhMjA3NjkyNSJ9.fKoGiiLytFlu9HgVRynoRMzK-U4A1WI5RCcrxsa4zRE"
req = urllib.request.Request('http://127.0.0.1:8080/api/contacts/', headers={'Authorization': f'Bearer {token}'})
try:
    res = urllib.request.urlopen(req)
    print("STATUS:", res.getcode())
    # print(res.read().decode())
except Exception as e:
    if hasattr(e, 'read'):
        print("ERROR:", e.code, e.read().decode())
    else:
        print("ERROR:", str(e))
