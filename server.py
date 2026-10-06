import os
import json
import time
import urllib.request
import urllib.error
import http.server
import socketserver


PORT = 8080

# Helper to load .env file if present
def load_dotenv():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

load_dotenv()

def is_dim_known(remembered, dim_name, valid_values=None):
    if not isinstance(remembered, dict):
        return False
    for k, v in remembered.items():
        if v is None:
            continue
        val_str = str(v).strip().lower()
        if val_str in ['', 'null', 'none', 'undefined', 'unknown']:
            continue
        key_str = str(k).strip().lower()
        if key_str == dim_name.lower():
            return True
        if valid_values and any(val_str == val.lower() for val in valid_values):
            return True
    return False


def get_fallback_interpretation(text):
    lower = text.lower()

    cafe_tokens = ['cafe', 'coffee', 'espresso', 'latte', 'roastery', 'cappuccino', 'patisserie', 'brew', 'bakery', 'cup', 'table', 'drink', 'food', 'breakfast']
    cities = {'hyderabad': 'Hyderabad', 'bengaluru': 'Bengaluru', 'bangalore': 'Bengaluru', 'mumbai': 'Mumbai', 'goa': 'Goa', 'chennai': 'Chennai'}
    areas = {'jubilee': 'Jubilee Hills', 'banjara': 'Banjara Hills', 'koramangala': 'Koramangala', 'indiranagar': 'Indiranagar', 'bandra': 'Bandra', 'kala ghoda': 'Kala Ghoda', 'madhapur': 'Madhapur'}
    months = {'january': 'January', 'february': 'February', 'march': 'March', 'april': 'April', 'may': 'May', 'june': 'June', 'july': 'July', 'august': 'August', 'september': 'September', 'october': 'October', 'november': 'November', 'december': 'December'}
    non_cafe_keywords = ['beach', 'ocean', 'sea', 'shack', 'mountain', 'hill', 'trek', 'hike', 'dog', 'cat', 'pet', 'document', 'receipt', 'bill', 'passport', 'id', 'airport', 'flight', 'car', 'bike', 'lake', 'park', 'monument', 'fort']

    detected_city = next((v for k, v in cities.items() if k in lower), None)
    detected_area = next((v for k, v in areas.items() if k in lower), None)
    detected_month = next((v for k, v in months.items() if k in lower), None)
    has_cafe_token = any(k in lower for k in cafe_tokens)
    has_non_cafe = any(k in lower for k in non_cafe_keywords) and not has_cafe_token

    has_valid_signal = (has_cafe_token or detected_city is not None or detected_area is not None or detected_month is not None) and not has_non_cafe

    remembered = {}
    if has_cafe_token:
        remembered["Setting"] = "Cafe"
    if 'quote' in lower or 'wall' in lower:
        remembered["Detail"] = "Wall Quote"
    if detected_city:
        remembered["City"] = detected_city
    if detected_area:
        remembered["Area"] = detected_area
    if detected_month:
        remembered["Month"] = detected_month

    unknown = []
    if not detected_city:
        unknown.append("Location (City)")
    if not detected_area:
        unknown.append("Area / Neighborhood")
    if not detected_month:
        unknown.append("When (Month)")
    if "Setting" not in remembered:
        unknown.append("Setting")

    result = {
        "venue_type": "cafe" if has_cafe_token else None,
        "is_cafe_related": has_valid_signal,
        "city": detected_city,
        "area": detected_area,
        "month": detected_month,
        "category": "cafe" if has_cafe_token else None,
        "remembered": remembered if remembered else {"Setting": "Cafe"},
        "unknown": unknown if unknown else ["Location (City)", "Area / Neighborhood", "When (Month)"],
        "recommended_next_dimension": "city" if not detected_city else ("area" if not detected_area else "month"),
        "reconstruction_prompt": "You don't need to remember everything. Let's work backwards from what you do remember.",
        "reconstruction_task_prompt": "Let's start with the location (city). Which location feels familiar?",
        "detected_objects": ["wall quote"] if ('quote' in lower or 'wall' in lower) else [],
        "confidence_score": 0.8 if has_valid_signal else 0.0,
        "source": "fallback"
    }

    return result

def call_gemini_api(memory_text, api_key):
    models = ["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    last_err = None

    prompt = f"""You are an AI visual memory reconstruction assistant for a photo retrieval MVP.
The dataset contains photo memories with metadata dimensions:
- City: Hyderabad, Bengaluru, Mumbai
- Area: Jubilee Hills, Banjara Hills, Koramangala, Indiranagar, Bandra, Kala Ghoda, Madhapur
- Month: January, February, March, April, May, June, July, August, September, October, November, December
- Category: cafe

Analyze the user's memory input: "{memory_text}"

Rules:
1. Set "is_cafe_related": true ONLY if the input mentions "cafe", "coffee", roasteries, patisseries, coffee drinks, OR explicitly mentions a valid photo metadata field (city: Hyderabad/Bengaluru/Mumbai, area: Jubilee Hills/Koramangala/Bandra/etc., month: January..December).
2. Standalone words like "quote", "text", "picture", "photo" by themselves are NOT metadata fields and NOT cafe tokens. Set "is_cafe_related": false unless accompanied by "cafe", "coffee", or a valid city/area/month.
3. Set "is_cafe_related": false for unrelated topics (beach, mountain, pets, documents, airport, flights, etc., or standalone non-metadata words).
4. Extract "remembered" dictionary (key-value pairs of what the user remembers, e.g. Setting: "Cafe", Detail: "Wall Quote", City: "Hyderabad" if mentioned). Do NOT list Category in "unknown" if Setting/Cafe is already remembered. Do NOT put keys with null/Unknown values into remembered.
5. Extract "unknown" array of missing memory aspects (e.g., ["Location (City)", "Area / Neighborhood", "When (Month)"]).
6. Recommend the first useful memory reconstruction dimension in "recommended_next_dimension": "city" if city is missing/unknown, else "area" or "month".
7. Generate a friendly "reconstruction_task_prompt" recommending this first task (e.g., "Let's start with the location (city). Which location feels familiar?").

Return ONLY a valid JSON object matching this structure:
{{
  "venue_type": string | null,
  "is_cafe_related": boolean,
  "city": string | null,
  "area": string | null,
  "month": string | null,
  "category": string | null,
  "remembered": object,
  "unknown": array of strings,
  "recommended_next_dimension": string | null,
  "reconstruction_prompt": string,
  "reconstruction_task_prompt": string,
  "confidence_score": number
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    data = json.dumps(payload).encode('utf-8')

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(raw_text)
                parsed["source"] = "gemini"
                parsed["model_used"] = model
                
                # Strict verification: must match cafe tokens or explicit metadata
                lower = memory_text.lower()
                cafe_tokens = ['cafe', 'coffee', 'espresso', 'latte', 'roastery', 'cappuccino', 'patisserie', 'brew', 'bakery']
                meta_words = ['hyderabad', 'bengaluru', 'bangalore', 'mumbai', 'jubilee', 'banjara', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
                
                has_cafe = any(k in lower for k in cafe_tokens)
                has_meta = any(k in lower for k in meta_words) or any(parsed.get(k) for k in ['city', 'area', 'month'])
                
                parsed["is_cafe_related"] = has_cafe or has_meta
                if not parsed["is_cafe_related"]:
                    parsed["category"] = None
                    parsed["venue_type"] = None
                elif has_cafe:
                    parsed["category"] = "cafe"

                # Filter out null/unknown keys from remembered dict
                if parsed.get("remembered") and isinstance(parsed["remembered"], dict):
                    cleaned_rem = {}
                    for k, v in parsed["remembered"].items():
                        if v is not None:
                            val_s = str(v).strip().lower()
                            if val_s not in ['', 'null', 'none', 'undefined', 'unknown']:
                                cleaned_rem[k] = v
                    parsed["remembered"] = cleaned_rem if cleaned_rem else {"Setting": "Cafe"}
                else:
                    parsed["remembered"] = {"Setting": "Cafe"}

                if "quote" in lower and "Detail" not in parsed["remembered"]:
                    parsed["remembered"]["Detail"] = "Wall Quote"

                city_known = is_dim_known(parsed["remembered"], "city", ['hyderabad', 'bengaluru', 'mumbai'])
                area_known = is_dim_known(parsed["remembered"], "area", ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara'])

                if not city_known:
                    parsed["recommended_next_dimension"] = "city"
                    parsed["reconstruction_task_prompt"] = "Let's start with the location (city). Which location feels familiar?"
                elif not area_known:
                    parsed["recommended_next_dimension"] = "area"
                    parsed["reconstruction_task_prompt"] = "Which area or neighborhood feels familiar?"

                if not parsed.get("unknown"):
                    parsed["unknown"] = ["Location (City)", "Area / Neighborhood", "When (Month)"]

                return parsed
        except Exception as e:
            print(f"[SERVER DEBUG] Model '{model}' failed: {e}")
            last_err = e
            continue

    raise last_err or Exception("All Gemini API models failed")



def get_fallback_next_cue(remembered, unknown, failed_cues, candidate_count, candidate_dimensions):
    city_known = is_dim_known(remembered, 'city', ['hyderabad', 'bengaluru', 'mumbai'])
    area_known = is_dim_known(remembered, 'area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara'])
    year_known = is_dim_known(remembered, 'year', ['2024', '2023'])
    month_known = is_dim_known(remembered, 'month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'])

    failed_set = set(failed_cues or [])

    avail_dims = []
    for d, vals in candidate_dimensions.items():
        if vals and len(vals) > 1:
            if d == 'city' and city_known: continue
            if d == 'area' and area_known: continue
            if d == 'year' and year_known: continue
            if d == 'month' and month_known: continue
            avail_dims.append(d)

    # 1. Default first location cue when City unknown
    if not city_known and 'city' not in failed_set and 'city' in avail_dims:
        return {
            "next_memory_dimension": "city",
            "reason": "City is unknown and provides the natural first location-level recognition cue.",
            "interaction_type": "recognition",
            "source": "fallback"
        }

    # 2. Prefer Area if City is known
    if city_known and not area_known and 'area' not in failed_set and 'area' in avail_dims:
        return {
            "next_memory_dimension": "area",
            "reason": "City is recovered. Prefer Area next to narrow neighborhood.",
            "interaction_type": "recognition",
            "source": "fallback"
        }

    # 3. Prefer Month if Year is known
    if year_known and not month_known and 'month' not in failed_set and 'month' in avail_dims:
        return {
            "next_memory_dimension": "month",
            "reason": "Year is recovered. Prefer Month next to narrow time of year.",
            "interaction_type": "recognition",
            "source": "fallback"
        }

    # 4. Prefer Year if Month is known
    if month_known and not year_known and 'year' not in failed_set and 'year' in avail_dims:
        return {
            "next_memory_dimension": "year",
            "reason": "Month is recovered. Prefer Year next to specify visit year.",
            "interaction_type": "recognition",
            "source": "fallback"
        }

    # 5. Pick any remaining unresolved dimension not in failed_cues
    unresolved = [d for d in ['city', 'area', 'year', 'month'] if d not in failed_set and d in avail_dims]
    if unresolved:
        dim = unresolved[0]
        return {
            "next_memory_dimension": dim,
            "reason": f"Selected next unresolved dimension '{dim}'.",
            "interaction_type": "recognition",
            "source": "fallback"
        }

    return {
        "next_memory_dimension": "context",
        "reason": "All major metadata dimensions resolved or evaluated. Transitioning to visit context memory cues.",
        "interaction_type": "selection",
        "source": "fallback"
    }


def call_gemini_recommend_next_cue(payload, api_key):
    models = ["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    
    remembered = payload.get('remembered', {})
    unknown = payload.get('unknown', [])
    failed_cues = payload.get('failed_cues', [])
    candidate_count = payload.get('candidate_count', 0)
    candidate_dimensions = payload.get('candidate_dimensions', {})

    prompt = f"""You are an AI visual memory reconstruction guide recommending the next recognition task.
Current Memory Reconstruction State:
- REMEMBERED / RECOVERED: {json.dumps(remembered)}
- STILL UNKNOWN: {json.dumps(unknown)}
- FAILED CUES (user selected 'Not sure' / 'None of these'): {json.dumps(failed_cues)}
- REMAINING CANDIDATE COUNT: {candidate_count}
- CANDIDATE VALUES AVAILABLE PER DIMENSION: {json.dumps(candidate_dimensions)}

Rules & Constraints:
1. Default first location cue when City is unknown: "city".
2. If City is known and Area is unknown (and Area not in failed_cues): prefer "area".
3. If Year is known and Month is unknown (and Month not in failed_cues): prefer "month".
4. If Month is known and Year is unknown (and Year not in failed_cues): prefer "year".
5. If both Year and Month are known, NEVER ask for Year or Month.
6. If City and Area are known, move to another unresolved dimension (year or month).
7. NEVER recommend a dimension that has already been recovered/known in REMEMBERED.
8. NEVER recommend a dimension in FAILED CUES unless all other dimensions have failed.
9. Do NOT ask for exact Time.

Return ONLY a valid JSON object matching this structure:
{{
  "next_memory_dimension": "city" | "area" | "year" | "month" | "category" | "context",
  "reason": string,
  "interaction_type": "recognition" | "selection"
}}"""

    payload_json = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    data = json.dumps(payload_json).encode('utf-8')

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
                parsed = json.loads(raw_text)
                parsed["source"] = "gemini"
                parsed["model_used"] = model

                # Server-side mandatory constraint enforcement
                city_known = is_dim_known(remembered, 'city', ['hyderabad', 'bengaluru', 'mumbai'])
                area_known = is_dim_known(remembered, 'area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara'])
                year_known = is_dim_known(remembered, 'year', ['2024', '2023'])
                month_known = is_dim_known(remembered, 'month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'])
                failed_set = set(failed_cues or [])

                if not city_known and 'city' not in failed_set:
                    parsed["next_memory_dimension"] = "city"
                    parsed["reason"] = "City is unknown. Location cue 'city' is the mandatory default first cue."
                elif city_known and not area_known and 'area' not in failed_set:
                    parsed["next_memory_dimension"] = "area"
                    parsed["reason"] = "City is recovered. Next location cue is 'area'."
                elif year_known and not month_known and 'month' not in failed_set:
                    parsed["next_memory_dimension"] = "month"
                    parsed["reason"] = "Year is recovered. Next time cue is 'month'."
                elif month_known and not year_known and 'year' not in failed_set:
                    parsed["next_memory_dimension"] = "year"
                    parsed["reason"] = "Month is recovered. Next time cue is 'year'."
                elif parsed.get("next_memory_dimension") in failed_set or is_dim_known(remembered, parsed.get("next_memory_dimension")):
                    unres = [d for d in ['city', 'area', 'year', 'month'] if d not in failed_set and not is_dim_known(remembered, d)]
                    parsed["next_memory_dimension"] = unres[0] if unres else "context"
                    parsed["reason"] = "Selected next unresolved dimension skipping failed cues."

                return parsed
        except Exception as e:
            print(f"[SERVER DEBUG] Recommend next cue model '{model}' failed: {e}")
            continue

    return get_fallback_next_cue(remembered, unknown, failed_cues, candidate_count, candidate_dimensions)


class SecureRetrievalServer(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/interpret':
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                body = json.loads(body_bytes.decode('utf-8'))
                memory_text = body.get('memoryText', '')
            except Exception:
                memory_text = ''

            load_dotenv()
            api_key = os.environ.get('GEMINI_API_KEY', '').strip()
            
            response_data = None
            if api_key:
                try:
                    print(f"[SERVER] Calling Gemini API for prompt: '{memory_text}'")
                    response_data = call_gemini_api(memory_text, api_key)
                    print(f"[SERVER] Gemini successfully returned interpretation: {response_data}")
                except Exception as e:
                    print(f"[SERVER WARNING] Gemini API call failed or timed out: {e}. Falling back to deterministic parser.")
                    response_data = get_fallback_interpretation(memory_text)

            else:
                print(f"[SERVER INFO] No GEMINI_API_KEY configured. Using deterministic fallback parser.")
                response_data = get_fallback_interpretation(memory_text)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        elif self.path == '/api/recommend_next_cue':
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                body = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                body = {}

            load_dotenv()
            api_key = os.environ.get('GEMINI_API_KEY', '').strip()
            
            response_data = None
            if api_key:
                try:
                    print(f"[SERVER] Calling Gemini API for next cue recommendation...")
                    response_data = call_gemini_recommend_next_cue(body, api_key)
                    print(f"[SERVER] Gemini successfully recommended next cue: {response_data}")
                except Exception as e:
                    print(f"[SERVER WARNING] Gemini recommend next cue call failed: {e}. Using fallback.")
                    response_data = get_fallback_next_cue(
                        body.get('remembered', {}),
                        body.get('unknown', []),
                        body.get('failed_cues', []),
                        body.get('candidate_count', 0),
                        body.get('candidate_dimensions', {})
                    )
            else:
                response_data = get_fallback_next_cue(
                    body.get('remembered', {}),
                    body.get('unknown', []),
                    body.get('failed_cues', []),
                    body.get('candidate_count', 0),
                    body.get('candidate_dimensions', {})
                )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SecureRetrievalServer) as httpd:
        print(f"==================================================")
        print(f"Secure Retrieval Server running at http://localhost:{PORT}")
        print(f"GEMINI_API_KEY configured: {'YES (Gemini Primary)' if os.environ.get('GEMINI_API_KEY') else 'NO (Fallback Active)'}")
        print(f"==================================================")
        httpd.serve_forever()
