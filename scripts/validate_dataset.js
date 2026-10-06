const fs = require('fs');
const path = require('path');

const datasetPath = path.join(__dirname, '../data/photos_dataset.json');

try {
  const rawData = fs.readFileSync(datasetPath, 'utf8');
  const photos = JSON.parse(rawData);

  console.log(`========================================`);
  console.log(`DATASET VALIDATION REPORT`);
  console.log(`========================================`);
  console.log(`Total Photos: ${photos.length}`);

  // Check required fields
  const requiredFields = [
    'id', 'url', 'title', 'city', 'area', 'venue_name',
    'venue_type', 'timestamp', 'people_present', 'activity',
    'scene_description', 'detected_objects', 'ocr_text',
    'visit_cluster_id', 'is_representative', 'is_target_photo'
  ];

  let missingCount = 0;
  let targetCount = 0;
  const cities = new Set();
  const areas = new Set();
  const venues = new Set();
  const clusters = new Set();

  photos.forEach((photo, index) => {
    requiredFields.forEach(field => {
      if (photo[field] === undefined || photo[field] === null) {
        console.error(`[ERROR] Photo at index ${index} (ID: ${photo.id}) missing field '${field}'`);
        missingCount++;
      }
    });

    cities.add(photo.city);
    areas.add(photo.area);
    venues.add(photo.venue_name);
    clusters.add(photo.visit_cluster_id);

    if (photo.is_target_photo) {
      targetCount++;
      console.log(`[TARGET PHOTO FOUND] ID: ${photo.id} | Title: "${photo.title}"`);
    }
  });

  console.log(`----------------------------------------`);
  console.log(`Unique Cities (${cities.size}):`, Array.from(cities));
  console.log(`Unique Areas (${areas.size}):`, Array.from(areas));
  console.log(`Unique Venues (${venues.size}):`, Array.from(venues));
  console.log(`Unique Visit Clusters (${clusters.size})`);
  console.log(`----------------------------------------`);

  if (targetCount === 1 && missingCount === 0) {
    console.log(`✅ DATASET VALIDATION PASSED SUCCESSFULLY!`);
  } else {
    console.error(`❌ DATASET VALIDATION FAILED! Target count: ${targetCount}, Missing fields: ${missingCount}`);
    process.exit(1);
  }
} catch (err) {
  console.error(`[FATAL] Unable to validate dataset:`, err.message);
  process.exit(1);
}
