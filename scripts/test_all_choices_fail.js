const fs = require('fs');
const path = require('path');

// Mock browser environment for engine testing
const dataset = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/photos_dataset.json'), 'utf8'));

// Minimal MemoryRetrievalEngine import simulation
const engineCode = fs.readFileSync(path.join(__dirname, '../js/engine.js'), 'utf8');
eval(engineCode);

const engine = new MemoryRetrievalEngine(dataset);

console.log("=== TEST: ALL CHOICES FAIL SCENARIO ===");

// 1. User starts with query "quote in a cafe I visited"
engine.applyIntent({ category: 'cafe', is_cafe_related: true }, "quote in a cafe I visited");

let candidates = engine.getFilteredCandidates();
console.log(`Initial cafe candidates count: ${candidates.length}`);

// 2. City cue presented -> User clicks "Not sure"
engine.applyFilter('city', 'UNSURE');
candidates = engine.getFilteredCandidates();
let nextDim = engine.getNextDiscriminator(candidates);
console.log(`After failing City -> Next discriminator: ${nextDim} (Failed cues: ${Array.from(engine.failedCues).join(', ')})`);

// 3. Year cue presented -> User clicks "Not sure"
engine.applyFilter('year', 'UNSURE');
candidates = engine.getFilteredCandidates();
nextDim = engine.getNextDiscriminator(candidates);
console.log(`After failing Year -> Next discriminator: ${nextDim} (Failed cues: ${Array.from(engine.failedCues).join(', ')})`);

// 4. Month cue presented -> User clicks "Not sure"
engine.applyFilter('month', 'UNSURE');
candidates = engine.getFilteredCandidates();
nextDim = engine.getNextDiscriminator(candidates);
console.log(`After failing Month -> Next discriminator: ${nextDim} (Failed cues: ${Array.from(engine.failedCues).join(', ')})`);

const allChoicesFailed = (!nextDim || nextDim === 'context') && engine.failedCues.size > 0 && candidates.length > 1;

if (allChoicesFailed) {
  console.log("✅ SUCCESS: System correctly detected that ALL choices failed!");
  engine.reset();
  console.log(`After reset -> Failed cues size: ${engine.failedCues.size}, Selected dims size: ${engine.selectedDimensions.size}`);
} else {
  console.error("❌ FAIL: System did not detect all choices failed!");
  process.exit(1);
}
