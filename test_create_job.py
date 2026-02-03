import requests
import json
import sys

# Configuration
URL = "http://localhost:8000/jobs"
TOKEN = "mock_test_token"  # Using mock prefix if required or just a placeholder
PAYLOAD_FILE = "test_payload.json"

def run_test():
    print(f"Testing POST {URL}...")
    
    # 1. Load Payload
    try:
        with open(PAYLOAD_FILE, "r") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PAYLOAD_FILE} not found.")
        sys.exit(1)

    # 2. Send Request
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(URL, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print("Response Body:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print("Response (Text):")
            print(response.text)
            
        if response.status_code == 200:
            print("\n✅ Test PASSED")
        else:
            print("\n❌ Test FAILED")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error. Is Docker running? (localhost:8000)")

if __name__ == "__main__":
    run_test()
