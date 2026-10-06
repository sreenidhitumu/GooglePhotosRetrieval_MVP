import urllib.request
import json

def test_api():
    url = 'http://localhost:8080/api/interpret'
    payload = json.dumps({"memoryText": "I remember a quote in a cafe"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("=== RESPONSE FROM /api/interpret ===")
        print(json.dumps(data, indent=2))

        assert "remembered" in data, "Missing 'remembered' field in response"
        assert "unknown" in data, "Missing 'unknown' field in response"
        print("\n✅ API verification PASSED! Response contains structured memory state (remembered & unknown).")

if __name__ == '__main__':
    test_api()
