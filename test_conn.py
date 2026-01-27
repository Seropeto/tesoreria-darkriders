import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_connectivity():
    print(f"Testing connectivity to {BASE_URL}...")
    try:
        # 1. Login
        print("1. Attempting Login...")
        login_data = urllib.parse.urlencode({'username': 'admin@darkriders.com', 'password': 'admin'}).encode()
        req = urllib.request.Request(f"{BASE_URL}/token", data=login_data, method='POST')
        
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"FAILED LOGIN. Status: {response.status}")
                return
            body = response.read().decode()
            token = json.loads(body).get('access_token')
            print(f"Login Success. Token: {token[:10]}...")

        # 2. Create Expense
        print("2. Creating Expense Transaction...")
        payload = {
            "amount": 1000,
            "type": "expense",
            "description": "Test Expense Script"
        }
        data = json.dumps(payload).encode('utf-8')
        
        req2 = urllib.request.Request(f"{BASE_URL}/transactions/", data=data, method='POST')
        req2.add_header('Authorization', f'Bearer {token}')
        req2.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req2) as response2:
            if response2.status == 200:
                print("SUCCESS. Expense Created.")
                print(response2.read().decode())
            else:
                print(f"FAILED. Status: {response2.status}")

    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: {e.code} - {e.read().decode()}")
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")

if __name__ == "__main__":
    test_connectivity()
