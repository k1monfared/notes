// Movie Writer PWA — local-first, batched-commit, inline-edit list view.
//
// Authentication and GitHub sync follow the same model as blog-writer
// (shared `gh_token` localStorage key, IndexedDB for offline state, debounced
// commits coalesced into a single message).
//
// UI: a flat list with four tabs (the four top-level sections of movies.log,
// rendered from the recursive Group parser). Tap a card to expand inline →
// status cycle, category dropdown, recommender, review, tags. Auto-routing
// moves the entry between sections silently as edits are made.

import { isAuthenticated, getToken, setToken, clearToken, validateToken } from './auth.js';
import { getFile, createCommit } from './github.js';
import {
  getLocalMovies, setLocalMovies,
  isDirty, setDirty,
  addPendingMessage, getPendingMessages, clearPendingMessages,
} from './storage.js';
import {
  parseMovies, walkMovies, findMovie, findInsertAfter,
  setStatus, setReview, setProperty, removeProperty,
  findToWatchInsert, buildMovieEntry,
} from './movies.js';
import {
  decideDestination, deriveRecommender, ensureRecommender, applyMove, autoRoute,
} from './route.js';

// ── Constants ────────────────────────────────────────────────────────────────

const RATED_CATEGORIES = [
  'I highly recommend',
  'I recommend',
  "I think it's a nice one",
  "There's something in it",
  'Good entertainment/fun and/or well-made',
  "I've watched it",
  'Not a good one',
  'I highly discourage',
  'to categorize',
];

const STATUS_CYCLE = { '': 'x', 'x': '-', '-': '?', '?': '' };
const STATUS_ICON  = { '': '☐', 'x': '✓', '-': '✗', '?': '?' };
const STATUS_LABEL = { '': 'unwatched', 'x': 'watched', '-': 'skipped', '?': 'uncertain' };

// ── State ────────────────────────────────────────────────────────────────────

const app = document.getElementById('app');
let moviesText = null;          // current local text
let parsed = { movies: [], roots: [] };
let activeTab = 'watched';      // root group name
let searchQuery = '';
let expandedKey = null;         // movie key (rootSection|title|index) currently expanded
let selectionMode = false;
let selectedKeys = new Set();
let syncInProgress = false;
let theme = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

// Filters
let filters = {
  yearBucket: 'all',  // 'all', '<2000', '2000s', '2010s', '2020s', etc.
  genres: new Set(),  // empty = all
  tags: new Set(),    // empty = all
  status: 'all',      // 'all', 'watched', 'unwatched', 'skipped', 'uncertain'
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function splitLines(text) {
  return text.split('\n').map((l, i, arr) => i < arr.length - 1 ? l + '\n' : (l ? l + '\n' : ''));
}

function joinLines(lines) {
  return lines.join('').replace(/\n$/, '');
}

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function movieKey(m, idx) {
  return `${slug(m.title)}|${idx}`;
}

// ── Local state I/O ──────────────────────────────────────────────────────────

async function loadLocal() {
  moviesText = await getLocalMovies();
  if (moviesText) {
    parsed = parseMovies(moviesText);
    return true;
  }
  return false;
}

async function saveLocal(text, commitMessage) {
  moviesText = text;
  parsed = parseMovies(text);
  await setLocalMovies(text);
  await setDirty(true);
  await addPendingMessage(commitMessage);
  updateSyncBadge();
  triggerSync();
}

async function fetchFromGitHub() {
  const file = await getFile('movies.log');
  moviesText = file.content;
  parsed = parseMovies(moviesText);
  if (!(await isDirty())) await setLocalMovies(moviesText);
  return true;
}

// Local mutation helper. fn(lines) -> lines'. Triggers sync + re-renders.
function mutateLocal(fn, commitMessage) {
  let lines = splitLines(moviesText);
  lines = fn(lines);
  if (!lines) return false;
  saveLocal(joinLines(lines), commitMessage);
  // Re-render tabs (counts) + the active list
  if (document.getElementById('tabs')) renderTabs();
  if (document.getElementById('movie-list')) {
    populateDatalists();
    renderFilters();
    renderList();
  }
  return true;
}

// ── Background sync (batched + retry) ────────────────────────────────────────

let syncTimeout = null;

function triggerSync() {
  if (syncTimeout) clearTimeout(syncTimeout);
  syncTimeout = setTimeout(() => doSync(), 1500);
}

async function doSync() {
  if (syncInProgress) return;
  if (!(await isDirty()) || !moviesText) return;

  syncInProgress = true;
  updateSyncBadge();

  try {
    const messages = await getPendingMessages();
    const message = messages.length === 1
      ? messages[0]
      : messages.slice(0, 5).join('; ') + (messages.length > 5 ? ` (+${messages.length - 5} more)` : '');

    await createCommit(
      [{ path: 'movies.log', content: moviesText }],
      message || 'Update movies'
    );

    await setDirty(false);
    await clearPendingMessages();

    // After sync, refetch from GitHub so local stays in sync with any
    // server-side enrichment / cleanup that ran on the workflow.
    if (!(await isDirty())) {
      try {
        await fetchFromGitHub();
        renderList();
      } catch { /* refetch is best-effort */ }
    }
  } catch (err) {
    console.error('Sync failed:', err);
  } finally {
    syncInProgress = false;
    updateSyncBadge();
  }
}

function updateSyncBadge() {
  const badge = document.getElementById('sync-badge');
  if (!badge) return;
  if (syncInProgress) {
    badge.textContent = 'syncing…';
    badge.className = 'sync-badge syncing';
    return;
  }
  isDirty().then(dirty => {
    if (!badge.isConnected) return;
    badge.textContent = dirty ? 'pending' : 'synced';
    badge.className = `sync-badge ${dirty ? 'pending' : 'synced'}`;
  });
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && isAuthenticated()) {
    isDirty().then(dirty => { if (dirty) triggerSync(); });
  }
});

// ── Theme toggle ─────────────────────────────────────────────────────────────

function applyTheme() {
  document.documentElement.dataset.theme = theme;
}
applyTheme();

function toggleTheme() {
  theme = theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', theme);
  applyTheme();
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = theme === 'dark' ? '☼' : '☾';
}

// ── Setup screen ─────────────────────────────────────────────────────────────

function showSetup() {
  app.innerHTML = `
    <div class="screen setup-screen">
      <h1>Movie Writer</h1>
      <p>Connect to your GitHub repo to manage your movie list.</p>
      <ol>
        <li>Go to <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">GitHub Token Settings</a></li>
        <li>Set token name to "Movie Writer"</li>
        <li>Select repository: <strong>k1monfared/notes</strong></li>
        <li>Under Permissions, set <strong>Contents: Read and write</strong></li>
        <li>Generate and paste the token below</li>
      </ol>
      <div class="form-group">
        <input type="password" id="token-input" placeholder="github_pat_..." autocomplete="off">
        <button id="connect-btn" class="btn primary">Connect</button>
      </div>
      <div id="setup-error" class="error" hidden></div>
    </div>
  `;
  const input = app.querySelector('#token-input');
  const btn = app.querySelector('#connect-btn');
  const errEl = app.querySelector('#setup-error');
  btn.addEventListener('click', async () => {
    const token = input.value.trim();
    if (!token) { errEl.textContent = 'Please enter a token'; errEl.hidden = false; return; }
    btn.disabled = true; btn.textContent = 'Validating…';
    const result = await validateToken(token);
    if (result.valid) { setToken(token); showList(); }
    else {
      errEl.textContent = result.error;
      errEl.hidden = false;
      btn.disabled = false; btn.textContent = 'Connect';
    }
  });
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') btn.click(); });
}

// ── Main list screen ─────────────────────────────────────────────────────────

async function showList(forceRefresh = false) {
  app.innerHTML = `
    <div class="screen list-screen">
      <header class="app-header">
        <h1>Movies</h1>
        <div class="header-actions">
          <span id="sync-badge" class="sync-badge"></span>
          <button id="theme-btn" class="btn icon" title="Toggle theme">${theme === 'dark' ? '☼' : '☾'}</button>
          <button id="refresh-btn" class="btn icon" title="Pull from GitHub">⟳</button>
          <button id="settings-btn" class="btn icon" title="Settings">⚙</button>
        </div>
      </header>
      <div id="tabs" class="tabs"></div>
      <div class="search-bar">
        <input type="text" id="search-input" placeholder="Search title, director, recommender…" autocomplete="off">
        <button id="add-btn" class="btn primary">+ Add</button>
      </div>
      <details id="filter-panel" class="filter-panel">
        <summary>Filters</summary>
        <div class="filter-body">
          <div class="filter-row" id="year-filters"></div>
          <div class="filter-row" id="genre-filters"></div>
          <div class="filter-row" id="tag-filters"></div>
          <div class="filter-row" id="status-filters"></div>
        </div>
      </details>
      <div id="movie-list" class="movie-list"></div>
      <div id="bulk-bar" class="bulk-bar" hidden></div>
      <datalist id="recommender-dl"></datalist>
      <datalist id="tag-dl"></datalist>
    </div>
  `;
  app.querySelector('#theme-btn').addEventListener('click', toggleTheme);
  app.querySelector('#refresh-btn').addEventListener('click', async () => {
    try { await fetchFromGitHub(); renderList(); }
    catch (err) { alert('Pull failed: ' + err.message); }
  });
  app.querySelector('#settings-btn').addEventListener('click', showSettings);
  app.querySelector('#add-btn').addEventListener('click', () => showAddModal());
  app.querySelector('#search-input').addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    renderList();
  });

  if (!(await loadLocal()) || forceRefresh) {
    try { await fetchFromGitHub(); }
    catch (err) {
      app.querySelector('#movie-list').innerHTML = `<div class="error">Failed to load: ${esc(err.message)}</div>`;
      return;
    }
  }
  // Default tab: pick the first non-empty root, prefer "watched"
  const tabNames = parsed.roots.map(r => r.name);
  if (tabNames.includes('watched')) activeTab = 'watched';
  else if (tabNames.length) activeTab = tabNames[0];

  // Hash deep-link: #m=<slug>
  const hashMatch = location.hash.match(/^#m=(.+)$/);
  if (hashMatch) {
    const target = decodeURIComponent(hashMatch[1]);
    const m = parsed.movies.find(x => slug(x.title) === target);
    if (m) {
      activeTab = m.rootSection || activeTab;
      expandedKey = movieKey(m, parsed.movies.indexOf(m));
    }
  }

  populateDatalists();
  renderTabs();
  renderFilters();
  renderList();
  updateSyncBadge();

  // Scroll expanded card into view (if hash deep-link)
  if (expandedKey) {
    setTimeout(() => {
      const el = document.querySelector(`[data-key="${CSS.escape(expandedKey)}"]`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  }
}

function renderTabs() {
  const el = document.getElementById('tabs');
  if (!el) return;
  el.innerHTML = parsed.roots.map(r => {
    const count = countInGroup(r);
    const isActive = r.name === activeTab;
    return `<button class="tab ${isActive ? 'active' : ''}" data-tab="${esc(r.name)}">${esc(r.name)} <span class="tab-count">${count}</span></button>`;
  }).join('');
  el.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab;
      renderTabs();
      renderList();
    });
  });
}

function countInGroup(g) {
  let n = g.movies.length;
  for (const c of g.children) n += countInGroup(c);
  return n;
}

function populateDatalists() {
  const recommenders = new Set();
  const tags = new Set();
  for (const m of parsed.movies) {
    if (m.props.recommenders) m.props.recommenders.forEach(r => recommenders.add(r));
    else if (m.props.recommender) recommenders.add(m.props.recommender);
    if (m.props.tags) m.props.tags.forEach(t => tags.add(t));
  }
  const recDl = document.getElementById('recommender-dl');
  if (recDl) recDl.innerHTML = [...recommenders].sort().map(r => `<option value="${esc(r)}">`).join('');
  const tagDl = document.getElementById('tag-dl');
  if (tagDl) tagDl.innerHTML = [...tags].sort().map(t => `<option value="${esc(t)}">`).join('');
}

function renderFilters() {
  // Year decade buckets
  const decades = new Map();
  for (const m of parsed.movies) {
    const y = parseInt(m.props.year, 10);
    if (!y) continue;
    const d = y < 2000 ? '<2000' : `${Math.floor(y / 10) * 10}s`;
    decades.set(d, (decades.get(d) || 0) + 1);
  }
  const yearOrder = ['<2000', '2000s', '2010s', '2020s', '2030s'].filter(d => decades.has(d));
  const yearEl = document.getElementById('year-filters');
  if (yearEl) {
    yearEl.innerHTML = `
      <span class="filter-label">Year:</span>
      <button class="chip ${filters.yearBucket === 'all' ? 'active' : ''}" data-year="all">all</button>
      ${yearOrder.map(d => `<button class="chip ${filters.yearBucket === d ? 'active' : ''}" data-year="${d}">${d} <span class="chip-count">${decades.get(d)}</span></button>`).join('')}
    `;
    yearEl.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
      filters.yearBucket = b.dataset.year;
      renderFilters(); renderList();
    }));
  }

  // Genres
  const genres = new Map();
  for (const m of parsed.movies) {
    if (!m.props.genres) continue;
    for (const g of m.props.genres.split(/[,/]/).map(s => s.trim().toLowerCase()).filter(Boolean)) {
      genres.set(g, (genres.get(g) || 0) + 1);
    }
  }
  const genreOrder = [...genres.keys()].sort();
  const genreEl = document.getElementById('genre-filters');
  if (genreEl) {
    genreEl.innerHTML = `
      <span class="filter-label">Genres:</span>
      ${genreOrder.map(g => `<button class="chip ${filters.genres.has(g) ? 'active' : ''}" data-genre="${esc(g)}">${esc(g)}</button>`).join('')}
    `;
    genreEl.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
      const g = b.dataset.genre;
      if (filters.genres.has(g)) filters.genres.delete(g); else filters.genres.add(g);
      renderFilters(); renderList();
    }));
  }

  // Tags
  const tags = new Map();
  for (const m of parsed.movies) {
    if (!m.props.tags) continue;
    for (const t of m.props.tags) tags.set(t, (tags.get(t) || 0) + 1);
  }
  const tagEl = document.getElementById('tag-filters');
  if (tagEl) {
    tagEl.innerHTML = `
      <span class="filter-label">Tags:</span>
      ${[...tags.keys()].sort().map(t => `<button class="chip ${filters.tags.has(t) ? 'active' : ''}" data-tag="${esc(t)}">${esc(t)}</button>`).join('') || '<span class="muted">(none yet)</span>'}
    `;
    tagEl.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
      const t = b.dataset.tag;
      if (filters.tags.has(t)) filters.tags.delete(t); else filters.tags.add(t);
      renderFilters(); renderList();
    }));
  }

  // Status
  const statusEl = document.getElementById('status-filters');
  if (statusEl) {
    const statuses = ['all', 'watched', 'unwatched', 'skipped', 'uncertain'];
    statusEl.innerHTML = `
      <span class="filter-label">Status:</span>
      ${statuses.map(s => `<button class="chip ${filters.status === s ? 'active' : ''}" data-status="${s}">${s}</button>`).join('')}
    `;
    statusEl.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
      filters.status = b.dataset.status;
      renderFilters(); renderList();
    }));
  }
}

function passesFilters(m) {
  // Year bucket
  if (filters.yearBucket !== 'all') {
    const y = parseInt(m.props.year, 10);
    if (!y) return false;
    const d = y < 2000 ? '<2000' : `${Math.floor(y / 10) * 10}s`;
    if (d !== filters.yearBucket) return false;
  }
  // Genres (any of selected)
  if (filters.genres.size) {
    const mg = (m.props.genres || '').split(/[,/]/).map(s => s.trim().toLowerCase());
    if (!mg.some(g => filters.genres.has(g))) return false;
  }
  // Tags (all of selected)
  if (filters.tags.size) {
    const mt = m.props.tags || [];
    for (const t of filters.tags) if (!mt.includes(t)) return false;
  }
  // Status
  if (filters.status !== 'all') {
    const s = STATUS_LABEL[m.status] || 'unwatched';
    if (s !== filters.status) return false;
  }
  // Search
  if (searchQuery) {
    const hay = [
      m.title, m.props.director, m.props.recommender, m.props.review,
      m.props.year, m.props.genres, m.props.country,
    ].filter(Boolean).join(' ').toLowerCase();
    if (!hay.includes(searchQuery)) return false;
  }
  return true;
}

function renderList() {
  const listEl = document.getElementById('movie-list');
  if (!listEl) return;
  // Movies in active tab
  const tabRoot = parsed.roots.find(r => r.name === activeTab);
  if (!tabRoot) { listEl.innerHTML = '<p class="empty">No movies in this section</p>'; return; }
  const flat = [];
  collectMovies(tabRoot, flat);
  const filtered = flat.filter(passesFilters);
  if (!filtered.length) {
    listEl.innerHTML = `<p class="empty">${searchQuery || filters.genres.size || filters.tags.size || filters.status !== 'all' || filters.yearBucket !== 'all' ? 'No matches' : 'No movies in this section'}</p>`;
    return;
  }

  // Group cards by category/subsection path for visual grouping
  const groups = new Map();  // 'Cat' or 'Cat / Sub' -> [movies]
  for (const m of filtered) {
    const key = m.subsection ? `${m.category} / ${m.subsection}` : (m.category || '');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(m);
  }

  let html = '';
  for (const [groupName, items] of groups) {
    if (groupName) html += `<div class="card-group-header">${esc(groupName)} <span class="muted">(${items.length})</span></div>`;
    html += items.map((m) => renderCard(m, parsed.movies.indexOf(m))).join('');
  }
  listEl.innerHTML = html;
  attachCardHandlers();
}

function collectMovies(group, out) {
  for (const m of group.movies) out.push(m);
  for (const c of group.children) collectMovies(c, out);
}

function renderCard(m, idx) {
  const key = movieKey(m, idx);
  const expanded = expandedKey === key;
  const selected = selectedKeys.has(key);
  const meta = [m.props.year, m.props.director?.split(',')[0]?.trim()].filter(Boolean).join(' · ');
  const recView = m.props.recommender ? ` · via ${esc(m.props.recommender)}` : '';
  const cls = `mv ${expanded ? 'expanded' : ''} ${selected ? 'selected' : ''}`;
  return `
    <div class="${cls}" data-key="${esc(key)}" data-idx="${idx}">
      <div class="mv-row" data-act="toggle">
        ${selectionMode ? `<input type="checkbox" class="mv-select" ${selected ? 'checked' : ''}>` : ''}
        <button class="mv-status" data-act="cycle" title="${STATUS_LABEL[m.status]}">${STATUS_ICON[m.status]}</button>
        <div class="mv-info">
          <div class="mv-title">${esc(m.title)}</div>
          ${meta || recView ? `<div class="mv-meta">${meta}${recView}</div>` : ''}
        </div>
        <span class="mv-arr">${expanded ? '▴' : '▾'}</span>
      </div>
      ${expanded ? renderDetail(m, idx) : ''}
    </div>
  `;
}

function renderDetail(m, idx) {
  const p = m.props;
  return `
    <div class="mv-detail">
      <div class="field-row">
        <label>Category</label>
        <select class="mv-category" data-idx="${idx}">
          <option value="">(unset)</option>
          ${RATED_CATEGORIES.map(c => `<option value="${esc(c)}" ${m.section === 'watched' && m.category === c ? 'selected' : ''}>${esc(c)}</option>`).join('')}
        </select>
      </div>
      <div class="field-row">
        <label>Recommender</label>
        <input type="text" class="mv-rec" list="recommender-dl" value="${esc(p.recommender || '')}" data-idx="${idx}">
      </div>
      <div class="field-row">
        <label>Year</label>
        <input type="text" class="mv-year" value="${esc(p.year || '')}" data-idx="${idx}">
      </div>
      <div class="field-row">
        <label>Director</label>
        <input type="text" class="mv-director" value="${esc(p.director || '')}" data-idx="${idx}">
      </div>
      <div class="field-row">
        <label>Review</label>
        <textarea class="mv-review" data-idx="${idx}">${esc(p.review || '')}</textarea>
      </div>
      <div class="field-row">
        <label>Tags</label>
        <input type="text" class="mv-tags" list="tag-dl" placeholder="comma,separated" value="${esc((p.tags || []).join(', '))}" data-idx="${idx}">
      </div>
      ${p.synopsis ? `<div class="detail-row"><strong>Synopsis</strong> ${esc(p.synopsis)}</div>` : ''}
      ${p.genres ? `<div class="detail-row"><strong>Genres</strong> ${esc(p.genres)}</div>` : ''}
      ${p.country ? `<div class="detail-row"><strong>Country</strong> ${esc(p.country)}</div>` : ''}
      ${p.duration ? `<div class="detail-row"><strong>Duration</strong> ${esc(p.duration)}</div>` : ''}
      ${p.cast?.length ? `<div class="detail-row"><strong>Cast</strong> ${esc(p.cast.slice(0, 5).join(', '))}</div>` : ''}
      ${p.imdb && p.imdb.startsWith('http') ? `<a class="imdb-link" href="${esc(p.imdb)}" target="_blank" rel="noopener">View on IMDB ↗</a>` : ''}
      <div class="mv-actions">
        <button class="btn small" data-act="save" data-idx="${idx}">Save</button>
        <button class="btn small danger" data-act="delete" data-idx="${idx}">Delete</button>
      </div>
    </div>
  `;
}

function attachCardHandlers() {
  document.querySelectorAll('.mv').forEach(card => {
    const idx = parseInt(card.dataset.idx, 10);
    const key = card.dataset.key;
    card.querySelector('[data-act="toggle"]')?.addEventListener('click', (e) => {
      // Don't toggle when clicking interactive children
      if (e.target.closest('.mv-status, .mv-select, button, input, select, textarea')) return;
      expandedKey = expandedKey === key ? null : key;
      renderList();
    });
    card.querySelector('[data-act="cycle"]')?.addEventListener('click', (e) => {
      e.stopPropagation();
      cycleStatus(idx);
    });
    card.querySelector('.mv-select')?.addEventListener('change', (e) => {
      e.stopPropagation();
      if (e.target.checked) selectedKeys.add(key);
      else selectedKeys.delete(key);
      updateBulkBar();
    });
    card.querySelector('[data-act="save"]')?.addEventListener('click', (e) => {
      e.stopPropagation();
      saveCardEdits(idx, card);
    });
    card.querySelector('[data-act="delete"]')?.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteMovie(idx);
    });
    card.querySelector('.mv-category')?.addEventListener('change', (e) => {
      e.stopPropagation();
      changeCategory(idx, e.target.value);
    });
  });
}

// ── Edit operations ──────────────────────────────────────────────────────────

function cycleStatus(idx) {
  const m = parsed.movies[idx];
  if (!m) return;
  const next = STATUS_CYCLE[m.status] ?? '';
  mutateLocal((lines) => {
    const found = findMovie(lines, m.title);
    if (!found) return null;
    setStatus(lines, found.index, next);
    // Re-parse after status flip to compute auto-route from fresh state
    const reparsed = parseMovies(joinLines(lines));
    const updated = reparsed.movies.find(x => x.title === m.title);
    if (!updated) return lines;
    const routed = autoRoute(lines, updated);
    return routed ? routed.lines : lines;
  }, `Cycle ${m.title}: ${STATUS_LABEL[m.status]} → ${STATUS_LABEL[next]}`);
}

function changeCategory(idx, category) {
  const m = parsed.movies[idx];
  if (!m) return;
  if (!category) return;  // ignore "(unset)"
  mutateLocal((lines) => {
    const found = findMovie(lines, m.title);
    if (!found) return null;
    // Re-parse to grab the entry shape
    const reparsed = parseMovies(joinLines(lines));
    const entry = reparsed.movies.find(x => x.title === m.title);
    if (!entry) return null;
    const out = applyMove(lines, entry, 'watched', category);
    return out;
  }, `Set category for ${m.title}: ${category}`);
}

function saveCardEdits(idx, cardEl) {
  const m = parsed.movies[idx];
  if (!m) return;
  const rec = cardEl.querySelector('.mv-rec')?.value.trim();
  const year = cardEl.querySelector('.mv-year')?.value.trim();
  const director = cardEl.querySelector('.mv-director')?.value.trim();
  const review = cardEl.querySelector('.mv-review')?.value.trim();
  const tagsStr = cardEl.querySelector('.mv-tags')?.value.trim();
  const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

  mutateLocal((lines) => {
    const found = findMovie(lines, m.title);
    if (!found) return null;
    if (rec !== undefined) {
      if (rec) setProperty(lines, found.index, found.indent, 'Recommender', rec);
      else removeProperty(lines, found.index, found.indent, 'Recommender');
    }
    if (year !== undefined) {
      if (year) setProperty(lines, found.index, found.indent, 'Year', year);
      else removeProperty(lines, found.index, found.indent, 'Year');
    }
    if (director !== undefined) {
      if (director) setProperty(lines, found.index, found.indent, 'Director', director);
      else removeProperty(lines, found.index, found.indent, 'Director');
    }
    if (review !== undefined) {
      if (review) setReview(lines, found.index, found.indent, review);
      else removeProperty(lines, found.index, found.indent, 'review');
    }
    if (tags.length) setProperty(lines, found.index, found.indent, 'tag', tags.join(', '));
    else removeProperty(lines, found.index, found.indent, 'tag');

    // Auto-route in case adding/removing review changed the destination
    const reparsed = parseMovies(joinLines(lines));
    const updated = reparsed.movies.find(x => x.title === m.title);
    if (!updated) return lines;
    const routed = autoRoute(lines, updated);
    return routed ? routed.lines : lines;
  }, `Update ${m.title}`);
}

function deleteMovie(idx) {
  const m = parsed.movies[idx];
  if (!m) return;
  showConfirmModal({
    title: 'Delete movie?',
    body: `<strong>${esc(m.title)}</strong>${m.props.year ? ' (' + esc(m.props.year) + ')' : ''} will be removed from movies.log.`,
    danger: true,
    confirmLabel: 'Delete',
    onConfirm: () => {
      mutateLocal((lines) => {
        const found = findMovie(lines, m.title);
        if (!found) return null;
        const end = findInsertAfter(lines, found.index, found.indent);
        lines.splice(found.index, end - found.index);
        return lines;
      }, `Delete ${m.title}`);
    },
  });
}

function showConfirmModal({ title, body, danger = false, confirmLabel = 'Confirm', cancelLabel = 'Cancel', onConfirm }) {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-card confirm-card">
      <h2>${esc(title)}</h2>
      <p class="confirm-body">${body}</p>
      <div class="modal-actions">
        <button class="btn" data-act="cancel">${esc(cancelLabel)}</button>
        <button class="btn ${danger ? 'danger' : 'primary'}" data-act="confirm" autofocus>${esc(confirmLabel)}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  const close = () => modal.remove();
  modal.querySelector('[data-act="cancel"]').addEventListener('click', close);
  modal.querySelector('[data-act="confirm"]').addEventListener('click', () => { close(); onConfirm(); });
  modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
  // Esc to close
  const onKey = (e) => { if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); } };
  document.addEventListener('keydown', onKey);
  // Focus the confirm button so Enter triggers it
  setTimeout(() => modal.querySelector('[data-act="confirm"]').focus(), 0);
}

// ── Add modal ────────────────────────────────────────────────────────────────

function showAddModal() {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-card">
      <h2>Add Movie</h2>
      <div class="form-group">
        <label>Title *</label>
        <input type="text" id="add-title" autofocus>
      </div>
      <div class="form-group">
        <label>Recommender</label>
        <input type="text" id="add-rec" list="recommender-dl">
      </div>
      <div class="form-group">
        <label>Director</label>
        <input type="text" id="add-director">
      </div>
      <div class="form-group">
        <label>Year</label>
        <input type="text" id="add-year">
      </div>
      <div class="form-group">
        <label>Review (optional)</label>
        <textarea id="add-review"></textarea>
      </div>
      <div class="modal-actions">
        <button class="btn" id="add-cancel">Cancel</button>
        <button class="btn primary" id="add-save">Add</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.querySelector('#add-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
  modal.querySelector('#add-save').addEventListener('click', () => {
    const title = modal.querySelector('#add-title').value.trim();
    if (!title) { alert('Title required'); return; }
    const recommender = modal.querySelector('#add-rec').value.trim();
    const director = modal.querySelector('#add-director').value.trim();
    const year = modal.querySelector('#add-year').value.trim();
    const review = modal.querySelector('#add-review').value.trim();

    if (findMovie(splitLines(moviesText), title)) {
      alert(`"${title}" already exists`);
      return;
    }
    mutateLocal((lines) => {
      const insert = findToWatchInsert(lines, recommender);
      if (!insert) { alert('Could not find insertion point'); return null; }
      let i = insert.index;
      if (insert.newLines) {
        for (const nl of insert.newLines) lines.splice(i++, 0, nl);
      }
      const entry = buildMovieEntry(title, { recommender, director, year, review }, insert.indent);
      lines.splice(i, 0, ...entry);
      return lines;
    }, `Add ${title}`);
    modal.remove();
  });
}

// ── Bulk-mark mode ───────────────────────────────────────────────────────────

function updateBulkBar() {
  const bar = document.getElementById('bulk-bar');
  if (!bar) return;
  if (selectedKeys.size === 0) {
    bar.hidden = true;
    selectionMode = false;
    renderList();
    return;
  }
  bar.hidden = false;
  bar.innerHTML = `
    <span>${selectedKeys.size} selected</span>
    <button class="btn small" data-bulk="x">Mark watched</button>
    <button class="btn small" data-bulk="-">Mark skipped</button>
    <button class="btn small" data-bulk="?">Mark uncertain</button>
    <button class="btn small" data-bulk="">Mark unwatched</button>
    <button class="btn small" data-bulk="cancel">Cancel</button>
  `;
  bar.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      const op = btn.dataset.bulk;
      if (op === 'cancel') { selectedKeys.clear(); selectionMode = false; updateBulkBar(); return; }
      bulkSetStatus(op);
    });
  });
}

function bulkSetStatus(status) {
  const titles = [];
  for (const key of selectedKeys) {
    const idx = parseInt(key.split('|')[1], 10);
    const m = parsed.movies[idx];
    if (m) titles.push(m.title);
  }
  if (!titles.length) return;
  mutateLocal((lines) => {
    for (const title of titles) {
      const found = findMovie(lines, title);
      if (!found) continue;
      setStatus(lines, found.index, status);
    }
    // Re-parse and auto-route everything that needs it
    let workingText = joinLines(lines);
    for (const title of titles) {
      const reparsed = parseMovies(workingText);
      const m = reparsed.movies.find(x => x.title === title);
      if (!m) continue;
      const routed = autoRoute(splitLines(workingText), m);
      if (routed) workingText = joinLines(routed.lines);
    }
    return splitLines(workingText);
  }, `Bulk ${STATUS_LABEL[status]}: ${titles.length} movies`);
  selectedKeys.clear();
  selectionMode = false;
  updateBulkBar();
}

// Long-press / shift-click to enter selection mode
document.addEventListener('contextmenu', (e) => {
  const card = e.target.closest('.mv');
  if (card) { e.preventDefault(); enterSelectionMode(card.dataset.key); }
});

function enterSelectionMode(initialKey) {
  selectionMode = true;
  if (initialKey) selectedKeys.add(initialKey);
  renderList();
  updateBulkBar();
}

// ── Settings screen ──────────────────────────────────────────────────────────

function showSettings() {
  app.innerHTML = `
    <div class="screen settings-screen">
      <header class="app-header">
        <button id="back-btn" class="btn icon">←</button>
        <h2>Settings</h2>
      </header>
      <div class="settings-body">
        <div class="form-group">
          <label>GitHub Token</label>
          <input type="password" value="${getToken() || ''}" readonly>
          <button id="disconnect-btn" class="btn danger">Disconnect</button>
        </div>
        <div class="form-group">
          <button id="force-sync-btn" class="btn full-width">Force Sync Now</button>
        </div>
        <div class="form-group">
          <p class="muted">Movie Writer PWA. Changes are saved locally and synced to GitHub in the background.</p>
        </div>
      </div>
    </div>
  `;
  app.querySelector('#back-btn').addEventListener('click', () => showList());
  app.querySelector('#disconnect-btn').addEventListener('click', () => {
    if (confirm('Disconnect from GitHub?')) { clearToken(); showSetup(); }
  });
  app.querySelector('#force-sync-btn').addEventListener('click', async () => {
    const btn = app.querySelector('#force-sync-btn');
    btn.disabled = true; btn.textContent = 'Syncing…';
    await doSync();
    btn.disabled = false; btn.textContent = 'Force Sync Now';
    alert(await isDirty() ? 'Sync failed, will retry.' : 'Synced!');
  });
}

// ── Hash routing ─────────────────────────────────────────────────────────────

window.addEventListener('hashchange', () => {
  const m = location.hash.match(/^#m=(.+)$/);
  if (m) {
    const target = decodeURIComponent(m[1]);
    const movie = parsed.movies.find(x => slug(x.title) === target);
    if (movie) {
      activeTab = movie.rootSection || activeTab;
      expandedKey = movieKey(movie, parsed.movies.indexOf(movie));
      renderTabs();
      renderList();
      setTimeout(() => {
        const el = document.querySelector(`[data-key="${CSS.escape(expandedKey)}"]`);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    }
  }
});

// ── Boot ─────────────────────────────────────────────────────────────────────

if (!isAuthenticated()) showSetup();
else showList();
