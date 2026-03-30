function showSection(id, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  if (id === 'top-cards') animateBars();
  if (id === 'clusters') setTimeout(animateArchetypeBars, 80);
}

// BAR CHART
function renderBars() {
  const c = document.getElementById('bar-chart-container');
  const max = DATA.top_cards[0].pct;
  c.innerHTML = DATA.top_cards.map(card => `
    <div class="bar-row">
      <div class="bar-name">${card.name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:0%" data-w="${card.pct/max*100}"></div></div>
      <div class="bar-pct">${card.pct}%</div>
    </div>`).join('');
}
function animateBars() {
  requestAnimationFrame(() => {
    document.querySelectorAll('#bar-chart-container .bar-fill').forEach(el => { el.style.width = el.dataset.w + '%'; });
  });
}

// CAPTAIN BARS
function renderCaptainBars() {
  const c = document.getElementById('captains-chart-container');
  if (!DATA.top_captains || DATA.top_captains.length === 0) {
    c.innerHTML = '<div style="color:var(--muted);font-size:12px;">No captain data available</div>';
    return;
  }
  const max = DATA.top_captains[0].freq;
  c.innerHTML = DATA.top_captains.map(cap => `
    <div class="bar-row">
      <div class="bar-name">${cap.name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:0%" data-w="${cap.freq/max*100}"></div></div>
      <div class="bar-pct">${cap.freq}</div>
    </div>`).join('');
}
function animateCaptainBars() {
  requestAnimationFrame(() => {
    document.querySelectorAll('#captains-chart-container .bar-fill').forEach(el => { el.style.width = el.dataset.w + '%'; });
  });
}
function setupCaptainObserver() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCaptainBars();
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  const container = document.getElementById('captains-chart-container');
  if (container) observer.observe(container);
}

// ARCHETYPE BARS
function renderArchetypeBars() {
  const c = document.getElementById('archetypes-chart-container');
  if (!DATA.top_archetypes || DATA.top_archetypes.length === 0) {
    c.innerHTML = '<div style="color:var(--muted);font-size:12px;">No archetype data available</div>';
    return;
  }
  const max = DATA.top_archetypes[0].freq;
  c.innerHTML = DATA.top_archetypes.map(arch => `
    <div class="bar-row">
      <div class="bar-name">${arch.name}</div>
      <div class="bar-track"><div class="bar-fill" style="background:${arch.color};width:0%" data-w="${arch.freq/max*100}"></div></div>
      <div class="bar-pct">${arch.freq}</div>
    </div>`).join('');
}
function animateArchetypeBars() {
  requestAnimationFrame(() => {
    document.querySelectorAll('#archetypes-chart-container .bar-fill').forEach(el => { el.style.width = el.dataset.w + '%'; });
  });
}

// CLUSTERS
function renderClusters() {
  const c = document.getElementById('clusters-container');
  c.innerHTML = DATA.clusters.map(cl => {
    const color = cl.color;
    let inner = '';
    if (cl.core) {
      inner = `
        <div class="subsection-label" style="color:${color}99">Core — high frequency</div>
        <div class="pills">${cl.core.map(card => pill(card, color, 0.8)).join('')}</div>
        <div class="subsection-label" style="color:${color}60;margin-top:14px">Situational — lower frequency</div>
        <div class="pills">${cl.situational.map(card => pill(card, color, 0.35)).join('')}</div>`;
    } else {
      inner = `<div class="pills">${cl.cards.map(card => pill(card, color, 0.7)).join('')}</div>`;
    }
    return `
      <div class="cluster-card">
        <div class="cluster-top-bar" style="background:${color};opacity:0.75"></div>
        <div class="cluster-header">
          <span class="cluster-label" style="color:${color}">${cl.label}</span>
          <span class="cluster-count">${(cl.core ? cl.core.length + cl.situational.length : cl.cards.length)} cards</span>
        </div>
        ${inner}
      </div>`;
  }).join('');
}
function pill(card, color, opacity) {
  return `<div class="pill" style="border-color:${color}${Math.round(opacity*99).toString(16).padStart(2,'0')}">
    <span>${card.name}</span><span class="pill-freq">${card.freq}</span>
  </div>`;
}

// CAPTAINS
function renderCaptains() {
  const c = document.getElementById('captains-container');

  // Build card name lookup and color mapping
  const cardInfo = {};
  const archColors = {};
  DATA.clusters.forEach(cl => {
    archColors[cl.label] = cl.color;
    // Handle both flat structure (cl.cards) and split structure (cl.core/cl.situational)
    if (cl.core) {
      // Split structure: core and situational arrays
      cl.core.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
      cl.situational.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
    } else if (cl.cards) {
      // Flat structure: single cards array
      cl.cards.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
    }
  });

  c.innerHTML = DATA.captains.map((cap, i) => {
    const uid = `cap-${i}`;
    const warn = cap.n < 5;

    // Track archetypes for filtering
    const archetypesPresent = cap.players ?
      [...new Set(cap.players.map(p => p.archetype))].join(' ') : '';

    // Signature rows (existing)
    const sigRows = cap.signature.map(tc => {
      const cls = tc.lift >= 10 ? 'lift-hi' : tc.lift >= 5 ? 'lift-mid' : 'lift-lo';
      const color = cardInfo[tc.card.replace(/\\s+/g, '_').toLowerCase()]?.color;
      return `<div class="lift-row">
        <div class="lift-name" style="color:${color || ''}">${tc.card}</div>
        <div class="lift-freq">${tc.freq}/${cap.n}</div>
        <div class="lift-badge ${cls}">${tc.lift}×</div>
      </div>`;
    }).join('');

    // Best 12 rows (existing)
    const bestRows = cap.best12.map(tc => {
      const color = cardInfo[tc.card.replace(/\\s+/g, '_').toLowerCase()]?.color;
      return `<div class="best-row">
        <div class="best-name" style="color:${color || ''}">${tc.card}</div>
        <div class="best-track">
          <div class="best-bar-wrap"><div class="best-bar-fill" style="width:${tc.pct}%"></div></div>
          <div class="best-pct">${tc.pct}%</div>
        </div>
      </div>`;
    }).join('');

    // Decklists view (new)
    const deckView = cap.players && cap.players.length > 0 ?
      `<div class="decklist-option-a">
        ${cap.players.map((p, pi) => `
          <div class="player-row" id="${uid}p${pi}" data-archetypes="${p.archetype}">
            <div class="player-row-header" onclick="togglePlayer('${uid}p${pi}')">
              <span class="player-username">${p.username}</span>
              <span class="tag" style="background:${archColors[p.archetype]}20; color:${archColors[p.archetype]}; border-color:${archColors[p.archetype]}40">
                ${p.archetype}
              </span>
              <span class="expand-icon">▶</span>
            </div>
            <div class="player-deck">
              <div class="deck-pills">
                ${p.deck.map(cardSlug => {
                  const info = cardInfo[cardSlug] || { name: cardSlug, color: '' };
                  return `<span class="deck-pill" style="${info.color ? 'color:' + info.color + 'cc;border-color:' + info.color + '30' : ''}">${info.name}</span>`;
                }).join('')}
              </div>
            </div>
          </div>
        `).join('')}
      </div>` :
      '<div style="padding:16px; color:var(--muted); font-size:11px;">No decklist data available</div>';

    return `
      <div class="captain-card" data-archetypes="${archetypesPresent}">
        <div class="captain-header">
          <div class="captain-name">${cap.name}</div>
          <div class="captain-n ${warn ? 'warn' : ''}">n=${cap.n}${warn ? ' ⚠' : ''}</div>
        </div>
        <div class="toggle-bar">
          <button class="toggle-btn active" onclick="switchView('${uid}','best',this)">Best 12</button>
          <button class="toggle-btn" onclick="switchView('${uid}','deck',this)">Decklists</button>
          <button class="toggle-btn" onclick="switchView('${uid}','sig',this)">Signature</button>
        </div>
        <div class="view active" id="${uid}-best"><div class="best-rows">${bestRows}</div></div>
        <div class="view" id="${uid}-deck">${deckView}</div>
        <div class="view" id="${uid}-sig"><div class="lift-rows">${sigRows}</div></div>
      </div>`;
  }).join('');
}

function switchView(uid, view, btn) {
  const card = btn.closest('.captain-card');
  card.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  card.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(`${uid}-${view}`).classList.add('active');
}

// Render archetype legend
function renderArchetypeLegend() {
  const c = document.getElementById('archetype-legend');
  const archetypes = Object.entries(DATA.cluster_map || {});
  c.innerHTML = `<span class="legend-label">Archetypes</span>` +
    archetypes.map(([label, color]) => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${color}"></div>
        ${label}
      </div>`).join('');
}

// Render captain filter
function renderCaptainFilter() {
  const c = document.getElementById('captain-filter');
  const archetypes = ['all', ...Object.keys(DATA.cluster_map || {})];
  c.innerHTML = `<span class="filter-label">Search</span>
    <input type="text" id="captain-search" class="filter-input" placeholder="Captain name..." oninput="filterCaptainsByText(this.value)">
    <span class="filter-label" style="margin-left:12px;">Show</span>` +
    archetypes.map(arch => `
      <button class="filter-btn ${arch === 'all' ? 'active' : ''}"
              onclick="filterCaptains('${arch}', this)">
        ${arch === 'all' ? 'All' : arch}
      </button>`).join('');
}

// Filter captains by archetype
function filterCaptains(key, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.captain-card').forEach(card => {
    if (key === 'all') {
      card.classList.remove('hidden');
    } else {
      const archs = card.dataset.archetypes || '';
      card.classList.toggle('hidden', !archs.includes(key));
    }
  });
}

// Filter captains by text search
function filterCaptainsByText(searchText) {
  const query = searchText.toLowerCase().trim();
  document.querySelectorAll('.captain-card').forEach(card => {
    const captainName = card.querySelector('.captain-name').textContent.toLowerCase();
    if (!query || captainName.includes(query)) {
      card.classList.remove('search-hidden');
    } else {
      card.classList.add('search-hidden');
    }
  });
}

// Toggle player row expansion
function togglePlayer(id) {
  const row = document.getElementById(id);
  row.classList.toggle('open');
}
