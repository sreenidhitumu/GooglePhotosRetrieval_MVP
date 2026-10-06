/**
 * Gemini Memory Interpreter Client Handler
 * Securely communicates with /api/interpret backend server
 */

class GeminiMemoryInterpreter {
  /**
   * Send memory text to secure backend endpoint /api/interpret
   */
  async interpretMemory(memoryText) {
    if (!memoryText || typeof memoryText !== 'string') {
      return this.getFallbackInterpretation(memoryText || '');
    }

    try {
      const res = await fetch('/api/interpret', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memoryText })
      });

      if (res.ok) {
        const data = await res.json();
        console.log(`[Interpreter Client] Interpretation source: ${data.source.toUpperCase()}`);
        return data;
      }
    } catch (err) {
      console.warn("[Interpreter Client] Network call to /api/interpret failed. Running client fallback:", err.message);
    }

    // Client-side fallback if server is unreachable
    return this.getFallbackInterpretation(memoryText);
  }

  /**
   * Client-side Fallback Parser
   */
  getFallbackInterpretation(text) {
    const lower = text.toLowerCase();
    const cafeKeywords = ['cafe', 'coffee', 'espresso', 'latte', 'quote', 'roastery', 'cappuccino', 'patisserie', 'brew', 'bakery', 'cup', 'table'];
    const nonCafeKeywords = ['beach', 'ocean', 'sea', 'shack', 'mountain', 'hill', 'trek', 'hike', 'dog', 'cat', 'pet', 'document', 'receipt', 'bill', 'passport', 'id', 'airport', 'flight', 'car', 'bike', 'lake', 'park', 'monument', 'fort'];

    const isCafe = cafeKeywords.some(k => lower.includes(k));
    const isNonCafe = nonCafeKeywords.some(k => lower.includes(k)) && !isCafe;

    const detected_city = lower.includes('hyderabad') ? 'Hyderabad' : (lower.includes('bengaluru') || lower.includes('bangalore') ? 'Bengaluru' : (lower.includes('mumbai') ? 'Mumbai' : (lower.includes('goa') ? 'Goa' : null)));
    const detected_area = lower.includes('jubilee') ? 'Jubilee Hills' : (lower.includes('banjara') ? 'Banjara Hills' : null);
    const detected_month = lower.includes('march') ? 'March' : (lower.includes('february') ? 'February' : (lower.includes('january') ? 'January' : null));

    const remembered = {};
    if (isCafe) remembered["Setting"] = "Cafe";
    if (lower.includes('quote') || lower.includes('wall')) remembered["Detail"] = "Wall Quote";
    if (detected_city) remembered["City"] = detected_city;
    if (detected_area) remembered["Area"] = detected_area;
    if (detected_month) remembered["Month"] = detected_month;

    const unknown = [];
    if (!detected_city) unknown.push("Where (City)");
    if (!detected_area) unknown.push("Area / Neighborhood");
    if (!detected_month) unknown.push("When (Month)");
    if (!remembered["Setting"]) unknown.push("Setting");

    const result = {
      venue_type: isCafe ? 'cafe' : (lower.includes('beach') ? 'beach' : 'other'),
      is_cafe_related: isCafe || !isNonCafe,
      city: detected_city,
      area: detected_area,
      month: detected_month,
      category: isCafe ? 'cafe' : null,
      remembered: Object.keys(remembered).length > 0 ? remembered : {"Setting": "Cafe"},
      unknown: unknown.length > 0 ? unknown : ["Where (City)", "Area / Neighborhood", "When (Month)"],
      recommended_next_dimension: !detected_city ? "city" : (!detected_area ? "area" : "month"),
      reconstruction_prompt: "You don't need to remember everything. Let's work backwards from what you do remember.",
      reconstruction_task_prompt: "Let's start with the city. Which location feels familiar?",
      detected_objects: (lower.includes('quote') || lower.includes('wall')) ? ['wall quote'] : [],
      confidence_score: 0.8,
      source: "fallback"
    };

    return result;
  }

  /**
   * Request Gemini recommendation for next memory cue based on current state & candidate space
   */
  async recommendNextCue(payload) {
    try {
      const res = await fetch('/api/recommend_next_cue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        console.log(`[Interpreter Client] Next Cue Recommendation: Gemini -> ${data.next_memory_dimension}`);
        return data;
      }
    } catch (err) {
      console.warn("[Interpreter Client] Network call /api/recommend_next_cue failed. Running fallback:", err.message);
    }

    return this.getFallbackNextCue(payload);
  }

  getFallbackNextCue(payload) {
    const remembered = payload.remembered || {};
    const failed_cues = payload.failed_cues || [];
    const candidate_dimensions = payload.candidate_dimensions || {};

    const isDimKnown = (dimName, validVals) => {
      for (const [k, v] of Object.entries(remembered)) {
        if (!v) continue;
        const valStr = String(v).trim().toLowerCase();
        if (['', 'null', 'none', 'undefined', 'unknown'].includes(valStr)) continue;
        if (k.trim().toLowerCase() === dimName.toLowerCase()) return true;
        if (validVals && validVals.some(val => val.toLowerCase() === valStr)) return true;
      }
      return false;
    };

    const city_known = isDimKnown('city', ['hyderabad', 'bengaluru', 'mumbai']);
    const area_known = isDimKnown('area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara']);
    const year_known = isDimKnown('year', ['2024', '2023']);
    const month_known = isDimKnown('month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']);

    const avail_dims = Object.keys(candidate_dimensions).filter(d => candidate_dimensions[d] && candidate_dimensions[d].length > 1);

    if (!city_known && !failed_cues.includes('city') && avail_dims.includes('city')) {
      return { next_memory_dimension: "city", reason: "City is unknown and provides natural location cue.", source: "fallback" };
    }
    if (city_known && !area_known && !failed_cues.includes('area') && avail_dims.includes('area')) {
      return { next_memory_dimension: "area", reason: "City is known. Prefer Area next.", source: "fallback" };
    }
    if (year_known && !month_known && !failed_cues.includes('month') && avail_dims.includes('month')) {
      return { next_memory_dimension: "month", reason: "Year is known. Prefer Month next.", source: "fallback" };
    }
    if (month_known && !year_known && !failed_cues.includes('year') && avail_dims.includes('year')) {
      return { next_memory_dimension: "year", reason: "Month is known. Prefer Year next.", source: "fallback" };
    }

    const unresolved = ['city', 'area', 'year', 'month'].filter(d => !failed_cues.includes(d) && !isDimKnown(d) && avail_dims.includes(d));
    if (unresolved.length > 0) {
      return { next_memory_dimension: unresolved[0], reason: `Selecting next unresolved dimension ${unresolved[0]}.`, source: "fallback" };
    }

    return { next_memory_dimension: "context", reason: "Transitioning to visit context memory cues.", source: "fallback" };
  }
}

// Export for browser and node environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GeminiMemoryInterpreter;
}
