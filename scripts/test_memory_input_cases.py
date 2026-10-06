import json
import re
import urllib.request

def is_valid_memory_input(text):
    if not text or not isinstance(text, str):
        return False
    trimmed = text.strip()
    if len(trimmed) == 0:
        return False
    if not re.search(r'[a-zA-Z]', trimmed):
        return False
    words = re.findall(r'[a-zA-Z]{2,}', trimmed)
    if not words:
        return False
    return True

def call_server_interpret(text):
    url = "http://localhost:8080/api/interpret"
    payload = json.dumps({"memoryText": text}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))

test_cases = [
    "7=",
    "12345",
    "beach photo",
    "mountain trip",
    "quote in a cafe I visited",
    "cafe in Hyderabad",
    "cafe in Chennai"
]

def run_tests():
    print("========================================")
    print("RUNNING MEMORY INPUT HANDLING TESTS")
    print("========================================\n")

    for text in test_cases:
        print(f'[TEST CASE] Input: "{text}"')
        valid = is_valid_memory_input(text)
        if not valid:
            print(f'  --> RESULT: INVALID_INPUT')
            print(f'  --> UI MESSAGE: "Tell me a little about what you remember about the photo."')
            print(f'  --> API CALLED: NO\n')
            continue

        try:
            intent = call_server_interpret(text)
            has_non_cafe = bool(re.search(r'beach|ocean|sea|shack|mountain|hike|trek|dog|cat|pet|document|receipt|bill|passport|airport|flight|car|bike|lake|park|monument|fort', text, re.IGNORECASE))
            has_cafe = bool(re.search(r'cafe|coffee|quote|espresso|roastery|latte|cappuccino|patisserie|brew|bakery', text, re.IGNORECASE))

            is_cafe_related = (intent.get("is_cafe_related") is not False) and (
                intent.get("is_cafe_related") is True or
                intent.get("venue_type") == 'cafe' or
                (has_cafe and not has_non_cafe) or
                (not has_non_cafe and intent.get("venue_type") not in ['beach', 'mountain', 'document'])
            )

            if not is_cafe_related:
                print(f'  --> RESULT: UNSUPPORTED_SCENARIO')
                print(f'  --> UI MESSAGE: "This prototype currently demonstrates cafe memories. Try a memory involving a cafe."')
                print(f'  --> SCOPE HINT: "Current demo: Cafe + Quote"\n')
            else:
                print(f'  --> RESULT: VALID_CAFE_QUERY')
                print(f'  --> INTENT: {intent}')
                print(f'  --> PROCEEDS TO DATASET FILTERING\n')
        except Exception as e:
            print(f'  --> ERROR calling server: {e}\n')

if __name__ == '__main__':
    run_tests()
