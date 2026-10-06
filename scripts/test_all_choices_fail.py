import json
import os

dataset_path = os.path.join(os.path.dirname(__file__), '../data/photos_dataset.json')
with open(dataset_path) as f:
    dataset = json.load(f)

CANDIDATE_DIMS = ['city', 'area', 'year', 'month', 'category']

class MockEngine:
    def __init__(self, photos):
        self.photos = photos
        self.active_filters = {}
        self.selected_dimensions = set()
        self.failed_cues = set()
        self.remembered = {}

    def is_dim_known(self, dim):
        return dim in self.selected_dimensions

    def apply_intent(self, category):
        self.active_filters['category'] = category
        self.selected_dimensions.add('category')
        self.remembered['Setting'] = category

    def apply_unsure(self, dimension):
        self.failed_cues.add(dimension)

    def get_candidates(self):
        res = []
        for p in self.photos:
            match = True
            for k, v in self.active_filters.items():
                if p.get(k) != v:
                    match = False
                    break
            if match:
                res.append(p)
        return res

    def get_next_discriminator(self, candidates):
        if len(candidates) <= 1:
            return None
        
        city_known = self.is_dim_known('city')
        if not city_known and 'city' not in self.failed_cues and 'city' not in self.selected_dimensions:
            return 'city'

        area_known = self.is_dim_known('area')
        if city_known and not area_known and 'area' not in self.failed_cues and 'area' not in self.selected_dimensions:
            return 'area'

        year_known = self.is_dim_known('year')
        month_known = self.is_dim_known('month')

        if year_known and not month_known and 'month' not in self.failed_cues and 'month' not in self.selected_dimensions:
            return 'month'
        if month_known and not year_known and 'year' not in self.failed_cues and 'year' not in self.selected_dimensions:
            return 'year'

        for dim in CANDIDATE_DIMS:
            if dim in self.selected_dimensions or dim in self.failed_cues:
                continue
            if dim == 'area' and not city_known:
                continue
            return dim
        return None

engine = MockEngine(dataset)
engine.apply_intent('cafe')

candidates = engine.get_candidates()
print(f"Initial candidates: {len(candidates)}")

# 1. City fails
engine.apply_unsure('city')
next_dim = engine.get_next_discriminator(candidates)
print(f"After City UNSURE -> next_dim: {next_dim}, failed_cues: {engine.failed_cues}")

# 2. Year fails
engine.apply_unsure('year')
next_dim = engine.get_next_discriminator(candidates)
print(f"After Year UNSURE -> next_dim: {next_dim}, failed_cues: {engine.failed_cues}")

# 3. Month fails
engine.apply_unsure('month')
next_dim = engine.get_next_discriminator(candidates)
print(f"After Month UNSURE -> next_dim: {next_dim}, failed_cues: {engine.failed_cues}")

all_choices_failed = (next_dim is None or next_dim == 'context') and len(engine.failed_cues) > 0 and len(candidates) > 1

if all_choices_failed:
    print("✅ SUCCESS: All choices failed condition correctly identified!")
else:
    print("❌ FAIL: Failure condition missed.")
