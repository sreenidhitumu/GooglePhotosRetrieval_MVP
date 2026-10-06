import os
import json
import time
import urllib.request
import urllib.error

env_path = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

api_key = os.environ.get('GEMINI_API_KEY', '')

models = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest"
]

print(f"Testing API key quota across models...")

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            print(f"✅ SUCCESS WITH '{model}':", res['candidates'][0]['content']['parts'][0]['text'])
            break
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code} for '{model}': {e.read().decode('utf-8')[:120]}")
    except Exception as e:
        print(f"❌ Exception for '{model}': {e}")
    time.sleep(1)
