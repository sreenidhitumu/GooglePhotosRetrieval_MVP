/**
 * Dynamic Discriminator & Candidate Filter Engine
 * AI-Guided Visual Memory Retrieval MVP
 */

class MemoryRetrievalEngine {
  constructor(dataset) {
    this.fullDataset = dataset;
    this.activeFilters = {};
    this.selectedDimensions = new Set();
    this.failedCues = new Set();
    this.candidateHistory = [];
    this.remembered = { "Setting": "Cafe" };
    this.unknown = ["Where (City)", "Area / Neighborhood", "Year", "When (Month)"];
  }

  /**
   * Reset engine state
   */
  reset() {
    this.activeFilters = {};
    this.selectedDimensions.clear();
    this.failedCues.clear();
    this.candidateHistory = [];
    this.remembered = { "Setting": "Cafe" };
    this.unknown = ["Where (City)", "Area / Neighborhood", "Year", "When (Month)"];
  }

  /**
   * Filter candidate photos strictly based on structured retrieval dimensions (city, area, year, month, category)
   */
  getMatchingCandidates() {
    return this.fullDataset.filter(photo => {
      for (const [key, filterVal] of Object.entries(this.activeFilters)) {
        if (!filterVal || filterVal === 'UNSURE' || filterVal === 'NONE') continue;

        if (Array.isArray(filterVal)) {
          if (filterVal.length === 0) continue;
          if (!filterVal.includes(photo[key])) return false;
        } else {
          const photoVal = String(photo[key] || '').toLowerCase();
          const searchVal = String(filterVal).toLowerCase();
          if (photoVal !== searchVal && !photoVal.includes(searchVal)) {
            return false;
          }
        }
      }
      return true;
    });
  }

  /**
   * Mark a cue dimension as failed ("Not sure" / "None of these")
   */
  markCueFailed(dimension) {
    if (dimension) {
      this.failedCues.add(dimension);
    }
  }

  /**
   * Get candidate dimensions summary for Gemini context
   */
  getCandidateDimensionsSummary(candidates) {
    const dims = ['city', 'area', 'year', 'month', 'category'];
    const summary = {};
    dims.forEach(d => {
      const vals = [...new Set(candidates.map(c => c[d]).filter(Boolean))];
      summary[d] = vals;
    });
    return summary;
  }

  /**
   * Apply intent parameters extracted by Gemini/LLM
   */
  applyIntent(intent, rawText) {
    this.candidateHistory.push({
      filters: { ...this.activeFilters },
      dimensions: new Set(this.selectedDimensions),
      failedCues: new Set(this.failedCues),
      remembered: { ...this.remembered },
      unknown: [ ...this.unknown ]
    });

    if (intent.remembered && typeof intent.remembered === 'object') {
      const cleaned = {};
      for (const [k, v] of Object.entries(intent.remembered)) {
        if (v !== null && v !== undefined) {
          const vStr = String(v).trim().toLowerCase();
          if (vStr !== '' && vStr !== 'null' && vStr !== 'undefined' && vStr !== 'unknown' && vStr !== 'none') {
            cleaned[k] = v;
          }
        }
      }
      this.remembered = { "Setting": "Cafe", ...cleaned };
    }

    if (intent.category || intent.venue_type || this.remembered["Setting"] || this.remembered["Category"]) {
      const catVal = intent.category || intent.venue_type || "cafe";
      this.activeFilters['category'] = catVal;
      this.selectedDimensions.add('category');
    }

    if (intent.city) {
      this.activeFilters['city'] = intent.city;
      this.selectedDimensions.add('city');
      this.remembered["City"] = intent.city;
    }
    if (intent.area) {
      this.activeFilters['area'] = intent.area;
      this.selectedDimensions.add('area');
      this.remembered["Area"] = intent.area;
    }
    if (intent.year) {
      this.activeFilters['year'] = intent.year;
      this.selectedDimensions.add('year');
      this.remembered["Year"] = intent.year;
    }
    if (intent.month) {
      this.activeFilters['month'] = intent.month;
      this.selectedDimensions.add('month');
      this.remembered["Month"] = intent.month;
    }

    this.rebuildUnknownList();
  }

  isDimKnown(dimName, validValues) {
    if (!this.remembered) return false;
    for (const [k, v] of Object.entries(this.remembered)) {
      if (v === null || v === undefined) continue;
      const valStr = String(v).trim().toLowerCase();
      if (valStr === '' || valStr === 'null' || valStr === 'undefined' || valStr === 'unknown' || valStr === 'none') {
        continue;
      }
      const keyStr = String(k).trim().toLowerCase();
      if (keyStr === dimName.toLowerCase()) return true;
      if (validValues && validValues.some(val => val.toLowerCase() === valStr)) return true;
    }
    return false;
  }

  rebuildUnknownList() {
    const list = [];
    if (!this.isDimKnown('city', ['hyderabad', 'bengaluru', 'mumbai'])) list.push('Location (City)');
    if (!this.isDimKnown('area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara'])) list.push('Area / Neighborhood');
    if (!this.isDimKnown('year', ['2024', '2023'])) list.push('Year');
    if (!this.isDimKnown('month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'])) list.push('When (Month)');
    this.unknown = list;
  }

  /**
   * Apply a new filter or refine selection
   */
  applyFilter(dimension, value) {
    this.candidateHistory.push({
      filters: { ...this.activeFilters },
      dimensions: new Set(this.selectedDimensions),
      failedCues: new Set(this.failedCues),
      remembered: { ...this.remembered },
      unknown: [ ...this.unknown ]
    });

    if (value === 'UNSURE' || value === 'NONE') {
      this.markCueFailed(dimension);
      return;
    }

    if (value) {
      this.activeFilters[dimension] = value;
      this.selectedDimensions.add(dimension);

      if (dimension === 'city') {
        this.remembered["City"] = value;
      } else if (dimension === 'area') {
        this.remembered["Area"] = value;
      } else if (dimension === 'year') {
        this.remembered["Year"] = value;
      } else if (dimension === 'month') {
        this.remembered["Month"] = value;
      } else if (dimension === 'category') {
        this.remembered["Setting"] = value;
      }

      this.rebuildUnknownList();
    }
  }

  /**
   * Revert last filter choice (Undo)
   */
  undoLastChoice() {
    if (this.candidateHistory.length === 0) return false;
    const previousState = this.candidateHistory.pop();
    this.activeFilters = previousState.filters;
    this.selectedDimensions = previousState.dimensions;
    if (previousState.failedCues) this.failedCues = previousState.failedCues;
    if (previousState.remembered) this.remembered = previousState.remembered;
    if (previousState.unknown) this.unknown = previousState.unknown;
    return true;
  }

  /**
   * Dynamically calculate the next best discriminator dimension based on current candidate subset
   * Dimensions: city, area, month, category
   */
  getNextDiscriminator(candidates) {
    if (candidates.length <= 1) return null;

    const cityKnown = this.isDimKnown('city', ['hyderabad', 'bengaluru', 'mumbai']);
    if (!cityKnown && !this.failedCues.has('city') && !this.selectedDimensions.has('city')) {
      return 'city';
    }

    const areaKnown = this.isDimKnown('area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara']);
    if (cityKnown && !areaKnown && !this.failedCues.has('area') && !this.selectedDimensions.has('area')) {
      return 'area';
    }

    const yearKnown = this.isDimKnown('year', ['2024', '2023']);
    const monthKnown = this.isDimKnown('month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']);

    if (yearKnown && !monthKnown && !this.failedCues.has('month') && !this.selectedDimensions.has('month')) {
      return 'month';
    }
    if (monthKnown && !yearKnown && !this.failedCues.has('year') && !this.selectedDimensions.has('year')) {
      return 'year';
    }

    const candidateDimensions = ['city', 'area', 'year', 'month', 'category'];
    let bestDimension = null;
    let bestScore = -1;

    for (const dim of candidateDimensions) {
      if (this.selectedDimensions.has(dim) || this.failedCues.has(dim) || this.isDimKnown(dim)) continue;
      if (dim === 'area' && !cityKnown) continue;

      const counts = {};
      for (const photo of candidates) {
        let val = photo[dim];
        if (!val) continue;
        counts[val] = (counts[val] || 0) + 1;
      }

      const values = Object.keys(counts);
      if (values.length <= 1) continue;

      let entropy = 0;
      const total = candidates.length;
      for (const val of values) {
        const p = counts[val] / total;
        entropy -= p * Math.log2(p);
      }

      if (entropy > bestScore) {
        bestScore = entropy;
        bestDimension = dim;
      }
    }

    if (!bestDimension) {
      for (const dim of candidateDimensions) {
        if (!this.selectedDimensions.has(dim) && !this.failedCues.has(dim) && !this.isDimKnown(dim)) {
          bestDimension = dim;
          break;
        }
      }
    }

    return bestDimension;
  }

  /**
   * Generate selectable recognition choices for a target dimension
   */
  generateChoices(candidates, dimension) {
    if (!dimension) return [];

    const counts = {};
    for (const photo of candidates) {
      let val = photo[dimension];
      if (!val) continue;
      counts[val] = (counts[val] || 0) + 1;
    }

    const options = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([val, count]) => ({
        label: val,
        value: val,
        count: count
      }));

    options.push({ label: "Not sure", value: "UNSURE", count: 0 });
    options.push({ label: "None of these", value: "NONE", count: 0 });

    return options;
  }

  /**
   * Group candidates by visit context and pick representative memory cues
   */
  getContextGroups(candidates) {
    const clusterMap = {};

    for (const photo of candidates) {
      const clusterId = photo.visit_cluster_id || `cluster_${photo.venue_name}_${photo.month}`;
      if (!clusterMap[clusterId]) {
        clusterMap[clusterId] = {
          cluster_id: clusterId,
          venue_name: photo.venue_name,
          city: photo.city,
          area: photo.area,
          category: photo.category,
          month: photo.month,
          photos: [],
          representative_photo: null
        };
      }
      clusterMap[clusterId].photos.push(photo);

      // Prioritize non-target photos for representative thumbnails
      if (!photo.is_target_photo) {
        if (photo.is_representative || !clusterMap[clusterId].representative_photo) {
          clusterMap[clusterId].representative_photo = photo;
        }
      }
    }

    // Fallback: if representative is still null (e.g. cluster only has target photo)
    for (const clusterId in clusterMap) {
      if (!clusterMap[clusterId].representative_photo && clusterMap[clusterId].photos.length > 0) {
        clusterMap[clusterId].representative_photo = clusterMap[clusterId].photos[0];
      }
    }

    return Object.values(clusterMap);
  }

}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = MemoryRetrievalEngine;
}
