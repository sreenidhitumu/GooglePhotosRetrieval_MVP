/**
 * Google Photos UI Controller & AI Memory Reconstruction Manager
 */

document.addEventListener('DOMContentLoaded', async () => {
  // -----------------------------------------------------------------------
  // DOM Elements: AI Reconstruction Tool
  // -----------------------------------------------------------------------
  const aiReconstructModal = document.getElementById('aiReconstructModal');
  const cantRememberBtn = document.getElementById('cantRememberBtn');
  const bannerTriggerBtn = document.getElementById('bannerTriggerBtn');
  const sidebarAiBtn = document.getElementById('sidebarAiBtn');
  const aiModalClose = document.getElementById('aiModalClose');
  const dismissBannerBtn = document.getElementById('dismissBannerBtn');
  const gpAiBanner = document.getElementById('gpAiBanner');

  const memoryInput = document.getElementById('memoryInput');
  const searchBtn = document.getElementById('searchBtn');
  const btnText = document.getElementById('btnText');
  const presetBtn = document.getElementById('presetBtn');
  const statusPanel = document.getElementById('statusPanel');
  const countBadge = document.getElementById('countBadge');
  const conversationalPrompt = document.getElementById('conversationalPrompt');
  const sourceBadge = document.getElementById('sourceBadge');
  const debugNextCueBadge = document.getElementById('debugNextCueBadge');
  const undoBtn = document.getElementById('undoBtn');
  const resetBtn = document.getElementById('resetBtn');

  // Dimension Picker & Choice Panels
  const dimPickerSection = document.getElementById('dimPickerSection');
  const dimButtons = document.querySelectorAll('.dim-btn');
  const choicePanel = document.getElementById('choicePanel');
  const choiceHeader = document.getElementById('choiceHeader');
  const chipsGrid = document.getElementById('chipsGrid');
  const gallerySection = document.getElementById('gallerySection');
  const galleryGrid = document.getElementById('galleryGrid');

  // Filtered Candidate Photos Grid inside Modal
  const filteredPhotosSection = document.getElementById('filteredPhotosSection');
  const filteredPhotosGrid = document.getElementById('filteredPhotosGrid');
  const photoGridCount = document.getElementById('photoGridCount');

  // Lightbox / Zoom Modal
  const photoModal = document.getElementById('photoModal');
  const modalClose = document.getElementById('modalClose');
  const modalTitle = document.getElementById('modalTitle');
  const modalSubtitle = document.getElementById('modalSubtitle');
  const modalPhotosGrid = document.getElementById('modalPhotosGrid');
  const modalSuccessBanner = document.getElementById('modalSuccessBanner');

  const zoomViewContainer = document.getElementById('zoomViewContainer');
  const zoomImage = document.getElementById('zoomImage');
  const zoomCaption = document.getElementById('zoomCaption');
  const zoomInBtn = document.getElementById('zoomInBtn');
  const zoomOutBtn = document.getElementById('zoomOutBtn');
  const zoomResetBtn = document.getElementById('zoomResetBtn');
  const zoomCloseBtn = document.getElementById('zoomCloseBtn');

  // Memory State Cards
  const memoryStateCard = document.getElementById('memoryStateCard');
  const rememberedChips = document.getElementById('rememberedChips');
  const unknownChips = document.getElementById('unknownChips');
  const failedChips = document.getElementById('failedChips');

  // Modal Notice Elements
  const aiModalNotice = document.getElementById('aiModalNotice');
  const aiModalNoticeText = document.getElementById('aiModalNoticeText');
  const aiModalNoticeClose = document.getElementById('aiModalNoticeClose');

  function showModalNotice(msg) {
    if (aiModalNoticeText) aiModalNoticeText.textContent = msg;
    if (aiModalNotice) aiModalNotice.style.display = 'flex';
  }

  function hideModalNotice() {
    if (aiModalNotice) aiModalNotice.style.display = 'none';
  }

  if (aiModalNoticeClose) {
    aiModalNoticeClose.addEventListener('click', hideModalNotice);
  }

  function performResetAll(noticeMessage) {
    if (engine) engine.reset();
    if (memoryInput) memoryInput.value = '';
    userOverrideDimension = null;
    if (statusPanel) statusPanel.style.display = 'none';
    if (memoryStateCard) memoryStateCard.style.display = 'none';
    if (dimPickerSection) dimPickerSection.style.display = 'none';
    if (choicePanel) choicePanel.style.display = 'none';
    if (gallerySection) gallerySection.style.display = 'none';
    if (filteredPhotosSection) filteredPhotosSection.style.display = 'none';
    if (undoBtn) undoBtn.style.display = 'none';

    if (noticeMessage) {
      showModalNotice(noticeMessage);
    } else {
      hideModalNotice();
    }
  }

  // Google Photos Stream Elements
  const gpPhotosStream = document.getElementById('gpPhotosStream');
  const gpTotalPhotosCount = document.getElementById('gpTotalPhotosCount');
  const gpSearchInput = document.getElementById('gpSearchInput');
  const gpSearchClearBtn = document.getElementById('gpSearchClearBtn');
  const filterChips = document.querySelectorAll('.gp-filter-chip');

  let dataset = [];
  let engine = null;
  let interpreter = null;
  let activeDiscriminator = null;
  let userOverrideDimension = null;
  let currentZoomScale = 1.0;
  let activeCategoryFilter = 'all';

  // -----------------------------------------------------------------------
  // Load Dataset & Initialize Engine
  // -----------------------------------------------------------------------
  try {
    const response = await fetch('data/photos_dataset.json');
    dataset = await response.json();
    engine = new MemoryRetrievalEngine(dataset);
    interpreter = new GeminiMemoryInterpreter();
    console.log(`[UI] Successfully loaded ${dataset.length} photo records.`);

    // Render Google Photos Main Library View
    renderGooglePhotosStream(dataset);
  } catch (err) {
    console.error("[UI] Failed to load dataset:", err);
  }

  // -----------------------------------------------------------------------
  // Google Photos Stream Renderer & Filters
  // -----------------------------------------------------------------------
  function renderGooglePhotosStream(photosToRender) {
    if (!gpPhotosStream) return;
    gpPhotosStream.innerHTML = '';

    if (gpTotalPhotosCount) {
      gpTotalPhotosCount.textContent = `${photosToRender.length} Photo${photosToRender.length !== 1 ? 's' : ''}`;
    }

    if (photosToRender.length === 0) {
      gpPhotosStream.innerHTML = `
        <div style="text-align: center; padding: 4rem 1rem; color: var(--gp-text-secondary);">
          <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔍</div>
          <h3 style="font-size: 1.2rem; color: #fff; margin-bottom: 0.5rem;">No matching photos in main library stream</h3>
          <p style="font-size: 0.9rem; margin-bottom: 1.25rem;">Try adjusting your search terms or use AI Memory Reconstruction to find vague memories.</p>
          <button id="streamAiTrigger" class="cant-remember-link" style="margin: 0 auto;">✨ Open AI Memory Reconstruction</button>
        </div>
      `;
      const streamAiTrigger = document.getElementById('streamAiTrigger');
      if (streamAiTrigger) {
        streamAiTrigger.addEventListener('click', openAiModal);
      }
      return;
    }

    // Group photos by Month & City
    const groups = {};
    photosToRender.forEach(photo => {
      const yearStr = photo.year || '2024';
      const groupKey = `${photo.month} ${yearStr} • ${photo.city}`;
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(photo);
    });

    // Render Grouped Stream
    Object.entries(groups).forEach(([groupName, photos]) => {
      const groupDiv = document.createElement('div');
      groupDiv.className = 'gp-date-group';

      const header = document.createElement('div');
      header.className = 'gp-date-header';
      header.innerHTML = `<span>📅 ${groupName}</span> <span style="font-size: 0.8rem; opacity: 0.6;">(${photos.length})</span>`;
      groupDiv.appendChild(header);

      const gridTiles = document.createElement('div');
      gridTiles.className = 'gp-grid-tiles';

      const orderedPhotos = pushTargetPhotoBeyondFirstRow(photos);

      orderedPhotos.forEach(photo => {
        const tile = document.createElement('div');
        tile.className = 'gp-photo-tile';

        tile.innerHTML = `
          <img src="${photo.url}" alt="${photo.title}" loading="lazy">
          <div class="gp-tile-overlay">
            <div class="gp-tile-title">${photo.title}</div>
            <div class="gp-tile-sub">📍 ${photo.venue_name} (${photo.area})</div>
          </div>
        `;

        tile.addEventListener('click', () => {
          openZoomView(photo);
        });

        gridTiles.appendChild(tile);
      });

      groupDiv.appendChild(gridTiles);
      gpPhotosStream.appendChild(groupDiv);
    });
  }

  function pushTargetPhotoBeyondFirstRow(photosList) {
    if (!photosList || photosList.length <= 1) return photosList;
    const nonTarget = [];
    const target = [];
    photosList.forEach(p => {
      if (p.is_target_photo) {
        target.push(p);
      } else {
        nonTarget.push(p);
      }
    });
    if (target.length === 0) return photosList;
    const insertIndex = Math.min(4, nonTarget.length);
    const result = [...nonTarget];
    result.splice(insertIndex, 0, ...target);
    return result;
  }

  // Google Photos Live Search Bar Input Listener
  if (gpSearchInput) {
    gpSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (gpSearchClearBtn) {
        gpSearchClearBtn.style.display = query ? 'block' : 'none';
      }

      if (!query) {
        applyCategoryFilter(activeCategoryFilter);
        return;
      }

      const filtered = dataset.filter(p => {
        const titleMatch = p.title.toLowerCase().includes(query);
        const cityMatch = p.city.toLowerCase().includes(query);
        const areaMatch = p.area.toLowerCase().includes(query);
        const venueMatch = p.venue_name.toLowerCase().includes(query);
        const monthMatch = p.month.toLowerCase().includes(query);
        const yearMatch = (p.year || '').toLowerCase().includes(query);
        const catMatch = p.category.toLowerCase().includes(query);
        const ocrMatch = p.ocr_text ? p.ocr_text.some(t => t.toLowerCase().includes(query)) : false;
        const objMatch = p.detected_objects ? p.detected_objects.some(t => t.toLowerCase().includes(query)) : false;

        return titleMatch || cityMatch || areaMatch || venueMatch || monthMatch || yearMatch || catMatch || ocrMatch || objMatch;
      });

      renderGooglePhotosStream(filtered);
    });
  }

  if (gpSearchClearBtn) {
    gpSearchClearBtn.addEventListener('click', () => {
      gpSearchInput.value = '';
      gpSearchClearBtn.style.display = 'none';
      applyCategoryFilter(activeCategoryFilter);
    });
  }

  // Quick Filter Chips Handler
  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activeCategoryFilter = chip.getAttribute('data-filter');
      applyCategoryFilter(activeCategoryFilter);
    });
  });

  function applyCategoryFilter(filterType) {
    if (filterType === 'all') {
      renderGooglePhotosStream(dataset);
    } else if (filterType === 'cafe') {
      renderGooglePhotosStream(dataset.filter(p => p.category === 'cafe'));
    } else if (filterType === 'hyderabad') {
      renderGooglePhotosStream(dataset.filter(p => p.city === 'Hyderabad'));
    } else if (filterType === 'bengaluru') {
      renderGooglePhotosStream(dataset.filter(p => p.city === 'Bengaluru'));
    } else if (filterType === 'mumbai') {
      renderGooglePhotosStream(dataset.filter(p => p.city === 'Mumbai'));
    } else if (filterType === 'quote') {
      renderGooglePhotosStream(dataset.filter(p => p.detected_objects && p.detected_objects.includes('framed wall quote')));
    }
  }

  // -----------------------------------------------------------------------
  // AI Memory Reconstruction Modal Handlers
  // -----------------------------------------------------------------------
  function openAiModal() {
    if (aiReconstructModal) {
      aiReconstructModal.style.display = 'flex';
      if (!memoryInput.value) {
        memoryInput.value = "quote in a cafe I visited";
      }
    }
  }

  function closeAiModal() {
    if (aiReconstructModal) {
      aiReconstructModal.style.display = 'none';
    }
  }

  if (cantRememberBtn) cantRememberBtn.addEventListener('click', openAiModal);
  if (bannerTriggerBtn) bannerTriggerBtn.addEventListener('click', openAiModal);
  if (sidebarAiBtn) sidebarAiBtn.addEventListener('click', (e) => {
    e.preventDefault();
    openAiModal();
  });

  if (aiModalClose) aiModalClose.addEventListener('click', closeAiModal);
  if (aiReconstructModal) {
    aiReconstructModal.addEventListener('click', (e) => {
      if (e.target === aiReconstructModal) {
        closeAiModal();
      }
    });
  }

  if (dismissBannerBtn && gpAiBanner) {
    dismissBannerBtn.addEventListener('click', () => {
      gpAiBanner.style.display = 'none';
    });
  }

  // Preset button handler
  if (presetBtn) {
    presetBtn.addEventListener('click', () => {
      memoryInput.value = "quote in a cafe I visited";
      handleInterpretation();
    });
  }

  // Search button handler
  if (searchBtn) searchBtn.addEventListener('click', handleInterpretation);

  // Undo button handler
  if (undoBtn) {
    undoBtn.addEventListener('click', async () => {
      if (engine.undoLastChoice()) {
        userOverrideDimension = null;
        await renderCurrentState();
      }
    });
  }

  // Reset button handler
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      performResetAll();
    });
  }

  // Dimension buttons handler
  dimButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const selectedDim = btn.getAttribute('data-dim');
      userOverrideDimension = selectedDim;
      
      dimButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      await renderCurrentState();
    });
  });

  // Close modal handler
  if (modalClose) {
    modalClose.addEventListener('click', () => {
      photoModal.classList.remove('active');
      modalSuccessBanner.style.display = 'none';
      hideZoomView();
    });
  }

  // Zoom controls
  if (zoomInBtn) zoomInBtn.addEventListener('click', () => {
    currentZoomScale = Math.min(3.5, currentZoomScale + 0.35);
    applyZoomScale();
  });

  if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => {
    currentZoomScale = Math.max(0.8, currentZoomScale - 0.35);
    applyZoomScale();
  });

  if (zoomResetBtn) zoomResetBtn.addEventListener('click', () => {
    currentZoomScale = 1.0;
    applyZoomScale();
  });

  if (zoomCloseBtn) zoomCloseBtn.addEventListener('click', hideZoomView);

  function applyZoomScale() {
    if (zoomImage) zoomImage.style.transform = `scale(${currentZoomScale})`;
  }

  function hideZoomView() {
    if (zoomViewContainer) zoomViewContainer.style.display = 'none';
    currentZoomScale = 1.0;
    applyZoomScale();
  }

  function openZoomView(photo) {
    if (!zoomImage || !photoModal) return;
    zoomImage.src = photo.url;
    if (zoomCaption) {
      const yearStr = photo.year || '2024';
      zoomCaption.textContent = `${photo.title} • ${photo.venue_name} (${photo.area}, ${photo.city}) • ${photo.month} ${yearStr}`;
    }
    currentZoomScale = 1.0;
    applyZoomScale();
    if (zoomViewContainer) zoomViewContainer.style.display = 'flex';

    if (photo.is_target_photo) {
      if (modalSuccessBanner) modalSuccessBanner.style.display = 'flex';
    } else {
      if (modalSuccessBanner) modalSuccessBanner.style.display = 'none';
    }

    photoModal.classList.add('active');
  }

  // -----------------------------------------------------------------------
  // Helper Functions & State Rendering
  // -----------------------------------------------------------------------
  function isValidMemoryInput(text) {
    if (!text || typeof text !== 'string') return false;
    const trimmed = text.trim();
    if (trimmed.length === 0) return false;
    if (!/[a-zA-Z]/.test(trimmed)) return false;
    const words = trimmed.match(/[a-zA-Z]{2,}/g);
    if (!words || words.length === 0) return false;
    return true;
  }

  function renderInvalidInputState() {
    statusPanel.style.display = 'flex';
    countBadge.style.display = 'none';
    if (sourceBadge) sourceBadge.style.display = 'none';
    if (debugNextCueBadge) debugNextCueBadge.style.display = 'none';
    undoBtn.style.display = 'none';

    conversationalPrompt.innerHTML = `
      <div style="color: var(--accent-amber); font-weight: 700; font-size: 1.15rem; margin-bottom: 0.3rem;">
        Tell me a little about what you remember about the photo.
      </div>
      <div style="font-size: 0.88rem; color: var(--text-secondary);">
        Please enter a description of a photo memory (e.g., "quote on a wall in a cafe").
      </div>
    `;

    if (memoryStateCard) memoryStateCard.style.display = 'none';
    if (dimPickerSection) dimPickerSection.style.display = 'none';
    choicePanel.style.display = 'none';
    gallerySection.style.display = 'none';
    filteredPhotosSection.style.display = 'none';
  }

  function renderUnsupportedScenarioState() {
    statusPanel.style.display = 'flex';
    countBadge.style.display = 'none';
    if (sourceBadge) sourceBadge.style.display = 'inline-flex';
    if (debugNextCueBadge) debugNextCueBadge.style.display = 'none';
    undoBtn.style.display = 'none';

    conversationalPrompt.innerHTML = `
      <div style="color: var(--accent-amber); font-weight: 700; font-size: 1.15rem; margin-bottom: 0.4rem;">
        This prototype currently demonstrates cafe memories. Try a memory involving a cafe.
      </div>
      <div style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.65rem; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 9999px; color: var(--accent-amber); font-size: 0.8rem; font-weight: 600;">
        ☕ Current demo: Cafe + Quote
      </div>
    `;

    if (memoryStateCard) memoryStateCard.style.display = 'none';
    if (dimPickerSection) dimPickerSection.style.display = 'none';
    choicePanel.style.display = 'none';
    gallerySection.style.display = 'none';
    filteredPhotosSection.style.display = 'none';
  }

  /**
   * Render Memory State Card (REMEMBERED / RECOVERED, STILL UNKNOWN, CUES NOT RECOGNIZED)
   */
  function renderMemoryStateBreakdown() {
    if (!engine || !memoryStateCard || !rememberedChips || !unknownChips) return;

    memoryStateCard.style.display = 'block';

    // 1. REMEMBERED / RECOVERED Chips
    rememberedChips.innerHTML = '';
    const rememberedEntries = Object.entries(engine.remembered || {});
    if (rememberedEntries.length === 0) {
      rememberedChips.innerHTML = `<span class="memory-badge memory-badge-remembered">Setting: Cafe</span>`;
    } else {
      rememberedEntries.forEach(([key, val]) => {
        const badge = document.createElement('span');
        badge.className = 'memory-badge memory-badge-remembered';
        badge.textContent = `${key}: ${val}`;
        rememberedChips.appendChild(badge);
      });
    }

    // 2. STILL UNKNOWN Chips
    unknownChips.innerHTML = '';
    const unknownList = engine.unknown || [];
    if (unknownList.length === 0) {
      unknownChips.innerHTML = `<span class="memory-badge memory-badge-remembered">✨ All metadata fragments recovered!</span>`;
    } else {
      unknownList.forEach(item => {
        const badge = document.createElement('span');
        badge.className = 'memory-badge memory-badge-unknown';
        badge.textContent = `❓ ${item}`;
        unknownChips.appendChild(badge);
      });
    }

    // 3. CUES NOT RECOGNIZED Chips
    if (failedChips) {
      failedChips.innerHTML = '';
      const failedList = Array.from(engine.failedCues || []);
      if (failedList.length === 0) {
        failedChips.innerHTML = `<span class="memory-badge" style="opacity: 0.5;">None</span>`;
      } else {
        failedList.forEach(item => {
          const badge = document.createElement('span');
          badge.className = 'memory-badge memory-badge-failed';
          badge.textContent = `⚠️ Not recognized: ${item.toUpperCase()}`;
          failedChips.appendChild(badge);
        });
      }
    }
  }

  /**
   * Main Memory Interpretation Handler
   */
  async function handleInterpretation() {
    const rawText = memoryInput.value;

    if (!isValidMemoryInput(rawText)) {
      renderInvalidInputState();
      return;
    }

    const text = rawText.trim();
    btnText.innerHTML = `<span class="loading-spinner"></span> Interpreting...`;
    searchBtn.disabled = true;

    hideModalNotice();

    try {
      const intent = await interpreter.interpretMemory(text);
      console.log("[UI] Interpreted intent:", intent);

      if (sourceBadge) {
        sourceBadge.style.display = 'none';
      }

      const textLower = text.toLowerCase();
      const cafeTokens = ['cafe', 'coffee', 'espresso', 'latte', 'roastery', 'cappuccino', 'patisserie', 'brew', 'bakery'];
      const metaWords = ['hyderabad', 'bengaluru', 'bangalore', 'mumbai', 'jubilee', 'banjara', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', '2024'];
      const nonCafeTokens = ['beach', 'ocean', 'sea', 'shack', 'mountain', 'hill', 'trek', 'hike', 'dog', 'cat', 'pet', 'document', 'receipt', 'bill', 'passport', 'id', 'airport', 'flight', 'car', 'bike', 'lake', 'park', 'monument', 'fort'];

      const hasCafeToken = cafeTokens.some(k => textLower.includes(k));
      const hasMeta = metaWords.some(k => textLower.includes(k)) || (intent && (intent.city || intent.area || intent.month || intent.year || intent.category === 'cafe'));
      const hasNonCafe = nonCafeTokens.some(k => textLower.includes(k)) && !hasCafeToken;

      const isRelevantToDataset = (hasCafeToken || hasMeta) && !hasNonCafe && (intent.is_cafe_related !== false);

      if (!isRelevantToDataset) {
        renderUnsupportedScenarioState();
        return;
      }

      engine.reset();
      userOverrideDimension = null;
      engine.applyIntent(intent, text);

      await renderCurrentState();
    } catch (err) {
      console.error("[UI] Interpretation error:", err);
    } finally {
      btnText.textContent = "Interpret Memory";
      searchBtn.disabled = false;
    }
  }

  /**
   * Render state dynamically based on active candidate set & Gemini cue recommendation
   */
  async function renderCurrentState() {
    const candidates = engine.getMatchingCandidates();
    const totalCount = candidates.length;

    statusPanel.style.display = 'flex';
    undoBtn.style.display = engine.candidateHistory.length > 0 ? 'inline-flex' : 'none';

    if (totalCount === 0) {
      countBadge.style.display = 'none';
      if (debugNextCueBadge) debugNextCueBadge.style.display = 'none';
      conversationalPrompt.innerHTML = `
        <div style="color: var(--accent-amber); font-weight: 700; font-size: 1.15rem; margin-bottom: 0.3rem;">
          No matching photos found in this prototype.
        </div>
        <div style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
          I searched the cafe photo library, but found zero photos matching those specific criteria.
        </div>
        <button id="resetFromZeroBtn" class="chip-preset" style="background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); font-weight: 600; padding: 0.4rem 0.9rem; border-radius: 6px; cursor: pointer;">
          🔄 Try another cafe query
        </button>
      `;

      setTimeout(() => {
        const resetBtn = document.getElementById('resetFromZeroBtn');
        if (resetBtn) {
          resetBtn.addEventListener('click', () => {
            engine.reset();
            memoryInput.value = '';
            userOverrideDimension = null;
            statusPanel.style.display = 'none';
            if (memoryStateCard) memoryStateCard.style.display = 'none';
            if (dimPickerSection) dimPickerSection.style.display = 'none';
            choicePanel.style.display = 'none';
            gallerySection.style.display = 'none';
            filteredPhotosSection.style.display = 'none';
          });
        }
      }, 50);

      if (memoryStateCard) memoryStateCard.style.display = 'none';
      if (dimPickerSection) dimPickerSection.style.display = 'none';
      choicePanel.style.display = 'none';
      gallerySection.style.display = 'none';
      filteredPhotosSection.style.display = 'none';
      return;
    }

    countBadge.style.display = 'inline-flex';
    countBadge.textContent = totalCount;

    if (totalCount === 1) {
      conversationalPrompt.textContent = "1 photo belongs to this reconstructed memory!";
    } else {
      conversationalPrompt.textContent = `${totalCount} photos could belong to this memory.`;
    }

    renderMemoryStateBreakdown();
    if (dimPickerSection) dimPickerSection.style.display = 'block';

    // Prepare state payload for Gemini /api/recommend_next_cue
    const statePayload = {
      remembered: engine.remembered,
      unknown: engine.unknown,
      failed_cues: Array.from(engine.failedCues),
      candidate_count: totalCount,
      candidate_dimensions: engine.getCandidateDimensionsSummary(candidates)
    };

    const recommendation = await interpreter.recommendNextCue(statePayload);
    console.log("[UI] Gemini Recommendation Payload:", recommendation);

    // Determine target discriminator dimension strictly adhering to location & time hierarchies
    const cityKnown = engine.isDimKnown('city', ['hyderabad', 'bengaluru', 'mumbai']);
    const areaKnown = engine.isDimKnown('area', ['jubilee hills', 'banjara hills', 'koramangala', 'indiranagar', 'bandra', 'kala ghoda', 'madhapur', 'jubilee', 'banjara']);
    const yearKnown = engine.isDimKnown('year', ['2024', '2023']);
    const monthKnown = engine.isDimKnown('month', ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']);

    let activeDim = null;

    if (userOverrideDimension && !engine.failedCues.has(userOverrideDimension) && !engine.isDimKnown(userOverrideDimension)) {
      activeDim = userOverrideDimension;
    } else if (!cityKnown && !engine.failedCues.has('city')) {
      // 1. Mandatory Location Hierarchy: City is default first cue
      activeDim = 'city';
    } else if (cityKnown && !areaKnown && !engine.failedCues.has('area')) {
      // 2. Mandatory Location Hierarchy: Area is second cue when City is known
      activeDim = 'area';
    } else if (yearKnown && !monthKnown && !engine.failedCues.has('month')) {
      // 3. Time Hierarchy: Month next when Year is known
      activeDim = 'month';
    } else if (monthKnown && !yearKnown && !engine.failedCues.has('year')) {
      // 4. Time Hierarchy: Year next when Month is known
      activeDim = 'year';
    } else if (recommendation && recommendation.next_memory_dimension && recommendation.next_memory_dimension !== 'context' && !engine.failedCues.has(recommendation.next_memory_dimension) && !engine.isDimKnown(recommendation.next_memory_dimension)) {
      activeDim = recommendation.next_memory_dimension;
    } else {
      activeDim = engine.getNextDiscriminator(candidates);
    }

    // Never ask for a dimension that has already been recovered or failed
    if (activeDim && activeDim !== 'context' && (engine.isDimKnown(activeDim) || engine.failedCues.has(activeDim))) {
      activeDim = engine.getNextDiscriminator(candidates);
    }

    activeDiscriminator = activeDim || 'context';

    // If all available choices/dimensions fail and we cannot recommend any further cue
    if ((!activeDim || activeDim === 'context') && engine.failedCues.size > 0 && totalCount > 1) {
      performResetAll("We couldn't reconstruct enough of this memory. Let's try again");
      return;
    }

    // Debug indicator badge hidden per UI requirements
    if (debugNextCueBadge) {
      debugNextCueBadge.style.display = 'none';
    }

    // Update active state on dimension buttons
    dimButtons.forEach(b => {
      const dim = b.getAttribute('data-dim');
      if (engine.selectedDimensions.has(dim)) {
        b.style.opacity = '0.5';
        b.style.cursor = 'not-allowed';
      } else {
        b.style.opacity = '1';
        b.style.cursor = 'pointer';
      }
      if (dim === userOverrideDimension || dim === activeDiscriminator) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });

    if (activeDiscriminator && activeDiscriminator !== 'context' && totalCount > 1) {
      renderChoicesPanel(candidates, activeDiscriminator);
    } else {
      choicePanel.style.display = 'none';
    }

    renderMemoryCueGallery(candidates);
    renderFilteredPhotosGrid(candidates);
  }

  /**
   * Render dynamic recognition choices (chips)
   */
  function renderChoicesPanel(candidates, dimension) {
    const options = engine.generateChoices(candidates, dimension);
    if (!options || options.length === 0) {
      choicePanel.style.display = 'none';
      return;
    }

    choicePanel.style.display = 'block';

    const formatDimensionLabel = (dim) => {
      switch (dim) {
        case 'city': return "🧠 AI Recommended Task: Let's start with the location (city). Which location feels familiar?";
        case 'area': return "🧠 AI Recommended Task: Which area or neighborhood feels familiar?";
        case 'year': return "🧠 AI Recommended Task: Which year feels familiar?";
        case 'month': return "🧠 AI Recommended Task: Which time of year or month feels familiar?";
        default: return "Which option looks familiar?";
      }
    };

    choiceHeader.textContent = formatDimensionLabel(dimension);
    chipsGrid.innerHTML = '';

    options.forEach(opt => {
      const chip = document.createElement('button');
      chip.className = `chip-choice ${opt.value === 'UNSURE' || opt.value === 'NONE' ? 'unsure' : ''}`;
      
      const labelSpan = document.createElement('span');
      labelSpan.textContent = opt.label;
      chip.appendChild(labelSpan);

      if (opt.count > 0) {
        const countSpan = document.createElement('span');
        countSpan.className = 'chip-count';
        countSpan.textContent = opt.count;
        chip.appendChild(countSpan);
      }

      chip.addEventListener('click', async () => {
        userOverrideDimension = null;
        engine.applyFilter(dimension, opt.value);
        await renderCurrentState();
      });

      chipsGrid.appendChild(chip);
    });
  }

  /**
   * Render context clusters as visual memory cues (Hides venue name until selected)
   */
  function renderMemoryCueGallery(candidates) {
    galleryGrid.innerHTML = '';
    const contexts = engine.getContextGroups(candidates);

    if (contexts.length === 0) {
      gallerySection.style.display = 'none';
      return;
    }

    gallerySection.style.display = 'block';

    contexts.forEach((context, idx) => {
      const rep = context.representative_photo;
      if (!rep) return;

      const card = document.createElement('div');
      card.className = 'context-card';

      card.innerHTML = `
        <div class="image-container">
          <img src="${rep.url}" alt="Memory Cue ${idx + 1}" loading="lazy">
          <span class="cue-tag">${context.photos.length} Photo${context.photos.length > 1 ? 's' : ''} in visit</span>
        </div>
        <div class="card-content">
          <div class="context-venue">Visit Memory Cue #${idx + 1}</div>
          <div class="context-location">📍 ${context.area}, ${context.city}</div>
          <div class="context-meta">
            <span>📅 ${context.month} ${rep.year || '2024'}</span>
            <span>Click to inspect visit context</span>
          </div>
        </div>
      `;

      card.addEventListener('click', () => {
        openContextModal(context);
      });

      galleryGrid.appendChild(card);
    });
  }

  /**
   * Render active filtered photos grid directly below memory cues
   */
  function renderFilteredPhotosGrid(candidates) {
    filteredPhotosGrid.innerHTML = '';
    photoGridCount.textContent = candidates.length;

    if (candidates.length === 0) {
      filteredPhotosSection.style.display = 'none';
      return;
    }

    filteredPhotosSection.style.display = 'block';

    const orderedCandidates = pushTargetPhotoBeyondFirstRow(candidates);

    orderedCandidates.forEach(photo => {
      const card = document.createElement('div');
      card.className = 'active-photo-card';

      card.innerHTML = `
        <img src="${photo.url}" alt="${photo.title}" loading="lazy">
        <div class="active-photo-meta">
          <div class="active-photo-title">${photo.title}</div>
          <div class="active-photo-sub">📍 ${photo.area}, ${photo.city} • 📅 ${photo.month} ${photo.year || '2024'}</div>
        </div>
      `;

      card.addEventListener('click', () => {
        openZoomView(photo);
      });

      filteredPhotosGrid.appendChild(card);
    });
  }

  /**
   * Open lightbox modal for context drill-down
   */
  function openContextModal(context) {
    const repYear = context.representative_photo ? (context.representative_photo.year || '2024') : '2024';
    modalTitle.textContent = `Memory Recovered: ${context.venue_name}`;
    modalSubtitle.textContent = `${context.area}, ${context.city} • ${context.month} ${repYear} • ${context.photos.length} photos in this visit`;
    modalPhotosGrid.innerHTML = '';
    modalSuccessBanner.style.display = 'none';
    hideZoomView();

    const orderedContextPhotos = pushTargetPhotoBeyondFirstRow(context.photos);

    orderedContextPhotos.forEach(photo => {
      const photoCard = document.createElement('div');
      photoCard.className = 'target-selectable-photo';

      photoCard.innerHTML = `
        <img src="${photo.url}" alt="${photo.title}">
        <div class="photo-caption">${photo.title}</div>
      `;

      photoCard.addEventListener('click', () => {
        openZoomView(photo);
      });

      modalPhotosGrid.appendChild(photoCard);
    });

    photoModal.classList.add('active');
  }
});
