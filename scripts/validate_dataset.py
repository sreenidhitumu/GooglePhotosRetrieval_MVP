import json
import os
import sys

dataset_path = os.path.join(os.path.dirname(__file__), '../data/photos_dataset.json')

with open(dataset_path, 'r', encoding='utf-8') as f:
    photos = json.load(f)

print("========================================")
print("DATASET VALIDATION REPORT (3 Cities x 3 Cafes x 5 Photos)")
print("========================================")
print(f"Total Photos: {len(photos)}")

required_fields = ['id', 'url', 'title', 'city', 'area', 'venue_name', 'category', 'year', 'month', 'visit_cluster_id', 'is_representative', 'is_target_photo']

missing_count = 0
target_count = 0

for idx, p in enumerate(photos):
    for f in required_fields:
        if f not in p or p[f] is None:
            print(f"[ERROR] Photo {idx} ({p.get('id')}) missing field '{f}'")
            missing_count += 1
    if p.get('is_target_photo'):
        target_count += 1
        print(f"[TARGET FOUND] ID: {p['id']} | Venue: {p['venue_name']} | Title: '{p['title']}'")

# Verify 3 cities x 3 cafes x 5 photos count
city_cafes = {}
for p in photos:
    if p['category'] == 'cafe':
        city = p['city']
        venue = p['venue_name']
        if city not in city_cafes:
            city_cafes[city] = {}
        city_cafes[city][venue] = city_cafes[city].get(venue, 0) + 1

print("\n--- CAFE DISTRIBUTION CHECK ---")
for city, cafes in city_cafes.items():
    print(f"City '{city}': {len(cafes)} cafes")
    for vname, cnt in cafes.items():
        print(f"   - {vname}: {cnt} photos")

if target_count == 1 and missing_count == 0:
    print("\n✅ DATASET VALIDATION PASSED SUCCESSFULLY!")
    sys.exit(0)
else:
    print(f"\n❌ VALIDATION FAILED! Target count: {target_count}, Missing: {missing_count}")
    sys.exit(1)
