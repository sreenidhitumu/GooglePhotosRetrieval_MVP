import json

with open('data/photos_dataset.json', 'r') as f:
    dataset = json.load(f)

print("========================================")
print("TESTING 4 RETRIEVAL DIMENSIONS (CITY, AREA, MONTH, CATEGORY)")
print(f"Total Dataset Size: {len(dataset)} photos")
print("========================================\n")

def filter_candidates(filters):
    candidates = []
    for photo in dataset:
        match = True
        for key, val in filters.items():
            if photo.get(key) != val:
                match = False
                break
        if match:
            candidates.append(photo)
    return candidates

test_cases = [
    ("City only", {"city": "Hyderabad"}),
    ("Area only", {"area": "Jubilee Hills"}),
    ("Month only", {"month": "March"}),
    ("Category only", {"category": "cafe"}),
    ("City + Month", {"city": "Hyderabad", "month": "March"}),
    ("City + Category", {"city": "Hyderabad", "category": "cafe"}),
    ("Area + Category", {"area": "Jubilee Hills", "category": "cafe"}),
    ("Month + Category", {"month": "March", "category": "cafe"}),
]

all_passed = True

for label, filters in test_cases:
    results = filter_candidates(filters)
    count = len(results)
    print(f"[TEST] {label} -> Filters: {filters}")
    print(f"       Matches: {count} photos")

    if count == 0:
        print(f"       ❌ FAILED! Zero candidates returned for valid filter: {filters}")
        all_passed = False
    elif count == len(dataset) and len(filters) > 0:
        print(f"       ❌ FAILED! Entire dataset ({len(dataset)}) returned for specific filter: {filters}")
        all_passed = False
    else:
        sample_venues = set(p['venue_name'] for p in results)
        print(f"       ✅ PASSED! Found {count} matching photos across venues: {sample_venues}\n")

if all_passed:
    print("========================================")
    print("ALL 8 DIMENSION FILTER COMBINATIONS PASSED PERFECTLY!")
    print("========================================")
else:
    print("❌ SOME TEST COMBINATIONS FAILED!")
