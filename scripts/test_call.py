import os
import json
import urllib.request

env_path = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

api_key = os.environ.get('GEMINI_API_KEY', '')

models = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]

prompt = """You are an AI visual memory assistant for a photo retrieval application.
Analyze the user's vague memory description and extract visual signals into a strict JSON object.

User Memory: "quote in a cafe I visited"

Return ONLY a valid JSON object matching this structure:
{
  "venue_type": "cafe" | "landmark" | "restaurant" | "park" | "market" | null,
  "city": string | null,
  "area": string | null,
  "detected_objects": string[],
  "activity": string | null,
  "confidence_score": number
}"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json"}
}
data = json.dumps(payload).encode('utf-8')

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
            print(f"SUCCESS with model '{model}':")
            print(raw_text)
            break
    except Exception as e:
        print(f"Failed with '{model}':", str(e))
