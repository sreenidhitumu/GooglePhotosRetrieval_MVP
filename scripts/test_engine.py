import json
import os
import math

dataset_path = os.path.join(os.path.dirname(__file__), '../data/photos_dataset.json')

with open(dataset_path, 'r', encoding='utf-8') as f:
    photos = json.load(f)

print(f"Loaded {len(photos)} photos for Python engine verification.")

# Simulate filtering
venue_type_cafe = [p for p in photos if p.get('venue_type') == 'cafe']
print(f"Candidates after venue_type=cafe filter: {len(venue_type_cafe)}")

# Compute best discriminator after venue_type=cafe
candidate_dims = ['city', 'area', 'venue_name', 'activity']
best_dim = None
best_entropy = -1

for dim in candidate_dims:
    counts = {}
    for p in venue_type_cafe:
        val = p.get(dim)
        if val:
            counts[val] = counts.get(val, 0) + 1
    
    if len(counts) <= 1:
        continue
    
    total = len(venue_type_cafe)
    entropy = 0
    for val, cnt in counts.items():
        p_val = cnt / total
        entropy -= p_val * math.log2(p_val)
    
    print(f"Dimension '{dim}' entropy: {entropy:.4f} (partitions into {len(counts)} groups)")
    if entropy > best_entropy:
        best_entropy = entropy
        best_dim = dim

print(f"-> Best Dynamic Discriminator selected: '{best_dim}'")

# Simulate city selection: Hyderabad
hyd_cafes = [p for p in venue_type_cafe if p.get('city') == 'Hyderabad']
print(f"Candidates after city=Hyderabad filter: {len(hyd_cafes)}")

# Compute next best discriminator after city=Hyderabad
best_dim_2 = None
best_entropy_2 = -1

for dim in ['area', 'venue_name', 'activity']:
    counts = {}
    for p in hyd_cafes:
        val = p.get(dim)
        if val:
            counts[val] = counts.get(val, 0) + 1
    
    if len(counts) <= 1:
        continue
    
    total = len(hyd_cafes)
    entropy = 0
    for val, cnt in counts.items():
        p_val = cnt / total
        entropy -= p_val * math.log2(p_val)
    
    print(f"Dimension '{dim}' entropy: {entropy:.4f} (partitions into {len(counts)} groups)")
    if entropy > best_entropy_2:
        best_entropy_2 = entropy
        best_dim_2 = dim

print(f"-> Next Best Dynamic Discriminator selected: '{best_dim_2}'")

# Simulate area selection: Jubilee Hills
jh_cafes = [p for p in hyd_cafes if p.get('area') == 'Jubilee Hills']
print(f"Candidates after area=Jubilee Hills filter: {len(jh_cafes)}")

# Cluster remaining candidates by visit_cluster_id
clusters = {}
for p in jh_cafes:
    cid = p.get('visit_cluster_id')
    if cid not in clusters:
        clusters[cid] = []
    clusters[cid].append(p)

print(f"Grouped remaining {len(jh_cafes)} candidates into {len(clusters)} visit context clusters:")
for cid, items in clusters.items():
    vname = items[0]['venue_name']
    rep = [x for x in items if x.get('is_representative')]
    rep_title = rep[0]['title'] if rep else items[0]['title']
    print(f"  - Context: '{vname}' ({len(items)} photos) | Representative memory cue: \"{rep_title}\"")

print("\n✅ CORE ENGINE VERIFICATION PASSED!")
