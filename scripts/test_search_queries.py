import json
import re
import urllib.request

with open('data/photos_dataset.json', 'r') as f:
    dataset = json.load(f)

def is_valid_memory_input(text):
    if not text or not isinstance(text, str): return False
    trimmed = text.strip()
    if len(trimmed) == 0: return False
    if not re.search(r'[a-zA-Z]', trimmed): return False
    words = re.findall(r'[a-zA-Z]{2,}', trimmed)
    return bool(words)

def call_server_interpret(text):
    url = "http://localhost:8080/api/interpret"
    payload = json.dumps({"memoryText": text}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))

def filter_dataset(intent):
    results = []
    for photo in dataset:
        match = True
        if intent.get("city") and photo.get("city") != intent["city"]:
            match = False
        if intent.get("area") and photo.get("area") != intent["area"]:
            match = False
        if intent.get("month") and photo.get("month") != intent["month"]:
            match = False
        if intent.get("category") and photo.get("category") != intent["category"]:
            match = False
        if match:
            results.append(photo)
    return results

test_queries = [
    "Hyderabad",
    "cafe",
    "quote in a cafe",
    "Jubilee Hills",
    "March",
    "Bengaluru",
    "Mumbai",
    "beach photo",
    "mountain trip",
    "7="
]

def run():
    print("========================================")
    print("TESTING METADATA SEARCH & DOMAIN RELEVANCE")
    print("========================================\n")

    for text in test_queries:
        print(f'[QUERY] "{text}"')
        if not is_valid_memory_input(text):
            print(f'  --> STATUS: INVALID_INPUT')
            print(f'  --> MESSAGE: "Tell me a little about what you remember about the photo."\n')
            continue

        try:
            intent = call_server_interpret(text)
            has_non_cafe = bool(re.search(r'beach|ocean|sea|shack|mountain|hike|trek|dog|cat|pet|document|receipt|bill|passport|airport|flight|car|bike|lake|park|monument|fort', text, re.IGNORECASE))
            has_meta = bool(re.search(r'hyderabad|bengaluru|bangalore|mumbai|jubilee|banjara|koramangala|indiranagar|bandra|kala ghoda|march|february|january|april|may|june|july|august|september|october|november|december|cafe|coffee|quote|espresso|roastery|latte|cappuccino|patisserie|brew|bakery', text, re.IGNORECASE))

            is_relevant = (intent.get("is_cafe_related") is not False) and (
                intent.get("is_cafe_related") is True or
                intent.get("venue_type") == 'cafe' or
                intent.get("city") is not None or
                intent.get("area") is not None or
                intent.get("month") is not None or
                intent.get("category") is not None or
                (has_meta and not has_non_cafe) or
                (not has_non_cafe and intent.get("venue_type") not in ['beach', 'mountain', 'document'])
            )

            if not is_relevant:
                print(f'  --> STATUS: UNSUPPORTED_SCENARIO')
                print(f'  --> MESSAGE: "This prototype currently demonstrates cafe memories. Try a memory involving a cafe."\n')
            else:
                matches = filter_dataset(intent)
                print(f'  --> STATUS: VALID_SEARCH_QUERY')
                print(f'  --> EXTRACTED INTENT: city={intent.get("city")}, area={intent.get("area")}, month={intent.get("month")}, category={intent.get("category")}')
                print(f'  --> MATCHING CANDIDATES: {len(matches)} photos\n')

        except Exception as e:
            print(f'  --> ERROR: {e}\n')

if __name__ == '__main__':
    run()
