import os
import json
import urllib.request
import urllib.error

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

api_key = os.environ.get('GEMINI_API_KEY', '')
print("API Key loaded:", api_key[:8] + "..." if api_key else "NONE")

# Test endpoints
models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.5-flash"
]

for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, respond with json: {\"status\": \"ok\"}"}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            print(f"✅ Success with model '{model}':", res_data['candidates'][0]['content']['parts'][0]['text'])
            break
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"❌ HTTP Error {e.code} for '{model}':", body[:200])
    except Exception as e:
        print(f"❌ Exception for '{model}':", str(e))
