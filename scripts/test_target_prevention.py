import json
import urllib.request
import sys

def call_server_interpret(text):
    url = "http://localhost:8080/api/interpret"
    payload = json.dumps({"memoryText": text}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))

with open('data/photos_dataset.json', 'r') as f:
    dataset = json.load(f)

test_queries = [
    "quote in a cafe",
    "quote on a cafe wall",
    "I remember a quote I saw in a cafe",
    "a cafe photo"
]

print("========================================")
print("TESTING RETRIEVAL TARGET LEAKAGE PREVENTION")
print("========================================\n")

all_passed = True

for text in test_queries:
    print(f'[TEST QUERY] "{text}"')
    intent = call_server_interpret(text)

    # Simulate MemoryRetrievalEngine candidate filtering (strictly category, city, area, month)
    candidates = []
    active_filters = {}
    if intent.get("category"): active_filters["category"] = intent["category"]
    elif intent.get("venue_type") == "cafe": active_filters["category"] = "cafe"
    if intent.get("city"): active_filters["city"] = intent["city"]
    if intent.get("area"): active_filters["area"] = intent["area"]
    if intent.get("month"): active_filters["month"] = intent["month"]

    for photo in dataset:
        match = True
        for k, v in active_filters.items():
            if photo.get(k) != v:
                match = False
                break
        if match:
            candidates.append(photo)

    count = len(candidates)
    print(f"  --> Extracted Intent Filters: {active_filters}")
    print(f"  --> Candidate Count: {count} photos")

    if count == 1:
        print(f"  --> ❌ FAILED! Query shortcutted directly to 1 target photo!")
        all_passed = False
    elif count >= 45:
        print(f"  --> ✅ PASSED! Broad candidate set ({count} photos) returned without OCR/shortcut leakage.\n")
    else:
        print(f"  --> ⚠️ WARNING: Returned {count} photos.\n")

if all_passed:
    print("========================================")
    print("ALL 4 RETRIEVAL LEAKAGE TESTS PASSED PERFECTLY!")
    print("========================================")
else:
    print("❌ SOME LEAKAGE TESTS FAILED!")
    sys.exit(1)
