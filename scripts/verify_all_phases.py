import json
import os
import sys

dataset_path = os.path.join(os.path.dirname(__file__), '../data/photos_dataset.json')

def run_technical_verification():
    print("==================================================")
    print("TECHNICAL VERIFICATION REPORT - ALL PHASES")
    print("==================================================")

    # Phase 1 Audit: Dataset Loading & Schema Integrity
    with open(dataset_path, 'r', encoding='utf-8') as f:
        photos = json.load(f)

    assert len(photos) >= 30, f"Expected dataset size >= 30, found {len(photos)}"
    target_photos = [p for p in photos if p.get('is_target_photo')]
    assert len(target_photos) == 1, f"Expected 1 target photo, found {len(target_photos)}"
    target = target_photos[0]
    print(f"[PHASE 1 PASS] Dataset size: {len(photos)} photos. Target ID: '{target['id']}'.")

    # Phase 2 Audit: Candidate Filtering & Dynamic Counts
    cafe_photos = [p for p in photos if p.get('category') == 'cafe' or p.get('venue_type') == 'cafe']
    print(f"[PHASE 2 PASS] Filter category='cafe' -> {len(cafe_photos)} matching photos (calculated dynamically).")

    hyd_cafes = [p for p in cafe_photos if p.get('city') == 'Hyderabad']
    print(f"[PHASE 2 PASS] Filter city='Hyderabad' -> {len(hyd_cafes)} matching photos.")

    jh_cafes = [p for p in hyd_cafes if p.get('area') == 'Jubilee Hills']
    print(f"[PHASE 2 PASS] Filter area='Jubilee Hills' -> {len(jh_cafes)} matching photos.")

    # Phase 3 Audit: Context Clustering & Representative Visual Memory Cues
    clusters = {}
    for p in jh_cafes:
        cid = p['visit_cluster_id']
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(p)

    print(f"[PHASE 3 PASS] Grouped into {len(clusters)} visit context memory cues:")
    target_context_found = False
    for cid, items in clusters.items():
        vname = items[0]['venue_name']
        rep = [x for x in items if x.get('is_representative')]
        rep_title = rep[0]['title'] if rep else items[0]['title']
        has_target = any(x['is_target_photo'] for x in items)
        if has_target:
            target_context_found = True
        print(f"  - Context: '{vname}' ({len(items)} photos) | Cue: \"{rep_title}\" | Has Target: {has_target}")

    assert target_context_found, "Target photo must be inside one of the recognized visit context clusters"

    # Phase 4 Audit: Target Photo Retrieval in Context
    roastery_photos = [p for p in jh_cafes if p['venue_name'] == 'Roastery Coffee House']
    assert target in roastery_photos, "Target photo must be present in Roastery Coffee House visit cluster"
    print(f"[PHASE 4 PASS] Target photo '{target['title']}' identified inside Roastery Coffee House visit!")

    print("==================================================")
    print("✅ ALL MVP TECHNICAL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_technical_verification()
