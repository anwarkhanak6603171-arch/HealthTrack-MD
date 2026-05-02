import urllib.request
import json

data = json.dumps({'username': 'testuser', 'password': 'testpass'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8001/register', data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as f:
        print(f.getcode())
        print(f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print(e)
