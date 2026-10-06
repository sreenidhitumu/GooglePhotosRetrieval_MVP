const http = require('http');

function isValidMemoryInput(text) {
  if (!text || typeof text !== 'string') return false;
  const trimmed = text.trim();
  if (trimmed.length === 0) return false;
  if (!/[a-zA-Z]/.test(trimmed)) return false;
  const words = trimmed.match(/[a-zA-Z]{2,}/g);
  if (!words || words.length === 0) return false;
  return true;
}

function callServerInterpret(text) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ memoryText: text });
    const req = http.request({
      hostname: 'localhost',
      port: 8080,
      path: '/api/interpret',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

const testCases = [
  "7=",
  "12345",
  "beach photo",
  "mountain trip",
  "quote in a cafe I visited",
  "cafe in Hyderabad",
  "cafe in Chennai"
];

async function runTests() {
  console.log("========================================");
  console.log("RUNNING MEMORY INPUT HANDLING TESTS");
  console.log("========================================\n");

  for (const text of testCases) {
    console.log(`[TEST CASE] Input: "${text}"`);
    const valid = isValidMemoryInput(text);
    if (!valid) {
      console.log(`  --> RESULT: INVALID_INPUT`);
      console.log(`  --> UI MESSAGE: "Tell me a little about what you remember about the photo."`);
      console.log(`  --> API CALLED: NO\n`);
      continue;
    }

    try {
      const intent = await callServerInterpret(text);
      const hasNonCafeKeyword = /beach|ocean|sea|shack|mountain|hike|trek|dog|cat|pet|document|receipt|bill|passport|airport|flight|car|bike|lake|park|monument|fort/i.test(text);
      const hasCafeKeyword = /cafe|coffee|quote|espresso|roastery|latte|cappuccino|patisserie|brew|bakery/i.test(text);

      const isCafeRelated = (intent.is_cafe_related !== false) && (
        intent.is_cafe_related === true ||
        intent.venue_type === 'cafe' ||
        (hasCafeKeyword && !hasNonCafeKeyword) ||
        (!hasNonCafeKeyword && intent.venue_type !== 'beach' && intent.venue_type !== 'mountain' && intent.venue_type !== 'document')
      );

      if (!isCafeRelated) {
        console.log(`  --> RESULT: UNSUPPORTED_SCENARIO`);
        console.log(`  --> UI MESSAGE: "This prototype currently demonstrates cafe memories. Try a memory involving a cafe."`);
        console.log(`  --> SCOPE HINT: "Current demo: Cafe + Quote"\n`);
      } else {
        console.log(`  --> RESULT: VALID_CAFE_QUERY`);
        console.log(`  --> INTENT:`, intent);
        console.log(`  --> PROCEEDS TO DATASET FILTERING\n`);
      }
    } catch (e) {
      console.error(`  --> ERROR calling server:`, e.message);
    }
  }
}

runTests();
