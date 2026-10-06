import json
import urllib.request
import re

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

test_queries = [
    ("Quote", False),  # Must NOT be accepted
    ("quote", False),  # Must NOT be accepted
    ("quote in a cafe", True),  # Must be accepted
    ("cafe", True),  # Must be accepted
    ("Hyderabad", True),  # Must be accepted
    ("beach photo", False)  # Must NOT be accepted
]

print("========================================")
print("TESTING STANDALONE 'QUOTE' REJECTION & METADATA SEARCH")
print("========================================\n")

for text, expected_valid in test_queries:
    print(f'[TEST QUERY] "{text}"')
    if not is_valid_memory_input(text):
        print(f'  --> STATUS: INVALID_INPUT')
        print(f'  --> MESSAGE: "Tell me a little about what you remember about the photo."\n')
        continue

    try:
        intent = call_server_interpret(text)
        has_non_cafe = bool(re.search(r'beach|ocean|sea|shack|mountain|hike|trek|dog|cat|pet|document|receipt|bill|passport|airport|flight|car|bike|lake|park|monument|fort', text, re.IGNORECASE))
        has_meta_keyword = bool(re.search(r'hyderabad|bengaluru|bangalore|mumbai|jubilee|banjara|koramangala|indiranagar|bandra|kala ghoda|march|february|january|april|may|june|july|august|september|october|november|december|cafe|coffee|espresso|roastery|latte|cappuccino|patisserie|brew|bakery', text, re.IGNORECASE))

        is_relevant = not has_non_cafe and (
            intent.get("is_cafe_related") is True or
            intent.get("venue_type") == 'cafe' or
            intent.get("city") is not None or
            intent.get("area") is not None or
            intent.get("month") is not None or
            intent.get("category") is not None or
            has_meta_keyword
        )

        if not is_relevant:
            print(f'  --> STATUS: UNSUPPORTED_SCENARIO')
            print(f'  --> UI MESSAGE: "This prototype currently demonstrates cafe memories. Try a memory involving a cafe."')
            if not expected_valid:
                print(f'  --> ✅ PASSED! Standalone "{text}" correctly rejected as unsupported.\n')
            else:
                print(f'  --> ❌ FAILED! Valid query "{text}" was rejected!\n')
        else:
            print(f'  --> STATUS: VALID_SEARCH_QUERY')
            print(f'  --> EXTRACTED INTENT: {intent}')
            if expected_valid:
                print(f'  --> ✅ PASSED! Query "{text}" accepted as valid metadata search.\n')
            else:
                print(f'  --> ❌ FAILED! Standalone "{text}" was incorrectly accepted as valid!\n')

    except Exception as e:
        print(f'  --> ERROR: {e}\n')
