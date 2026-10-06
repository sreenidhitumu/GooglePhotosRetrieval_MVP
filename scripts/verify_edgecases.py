import json
import os

dataset_path = os.path.join(os.path.dirname(__file__), '../data/photos_dataset.json')

with open(dataset_path, 'r', encoding='utf-8') as f:
    photos = json.load(f)

def test_query(query_str):
    kw = query_str.lower().split()
    matched = []
    for p in photos:
        searchable = f"{p['title']} {p['city']} {p['area']} {p['venue_name']} {p['venue_type']} {p['scene_description']} {p['activity']} {' '.join(p['detected_objects'])} {' '.join(p['ocr_text'])}".lower()
        if any(w in searchable for w in kw if len(w) > 2):
            matched.append(p)
    return matched

print("========================================")
print("EDGE CASE FILTER VERIFICATION")
print("========================================")

# 1. Query: "beach"
beach_matches = test_query("beach")
print(f"Query 'beach' matched {len(beach_matches)} photo(s):")
for m in beach_matches:
    print(f"  - ID: {m['id']} | Venue: {m['venue_name']} | Title: '{m['title']}'")
assert all(m['venue_type'] != 'cafe' for m in beach_matches), "Beach query must NOT return cafe photos!"

# 2. Query: "snowy mountain" (Irrelevant)
irrelevant_matches = test_query("snowy mountain")
print(f"\nQuery 'snowy mountain' matched {len(irrelevant_matches)} photo(s).")
assert len(irrelevant_matches) == 0, "Irrelevant query must return 0 candidates!"

print("\n✅ EDGE CASE FILTER VERIFICATION PASSED!")
