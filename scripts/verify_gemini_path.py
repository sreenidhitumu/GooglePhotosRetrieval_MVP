import os
import json
import urllib.request

def test_fallback_path():
    print("--- 1. Testing Fallback Path (No API Key) ---")
    url = "http://localhost:8080/api/interpret"
    data = json.dumps({"memoryText": "quote in a cafe I visited"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Fallback Response:", res)
        assert res.get('source') == 'fallback', "Expected source='fallback'"
        assert res.get('venue_type') == 'cafe', "Expected venue_type='cafe'"
        print("✅ Fallback path verified successfully!")

def test_gemini_path(api_key):
    print("\n--- 2. Testing Live Gemini 1.5 Flash Path ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
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
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

    with urllib.request.urlopen(req, timeout=10) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        parsed = json.loads(raw_text)
        parsed["source"] = "gemini"
        print("Live Gemini 1.5 Flash Response:", json.dumps(parsed, indent=2))
        assert parsed.get('venue_type') == 'cafe', "Expected venue_type='cafe'"
        print("✅ Live Gemini 1.5 Flash API path verified successfully!")
        return parsed

if __name__ == '__main__':
    test_fallback_path()
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        test_gemini_path(api_key)
    else:
        print("\n[INFO] GEMINI_API_KEY environment variable is not set.")
        print("To verify live Gemini calls, set GEMINI_API_KEY=your_key and run this script.")
