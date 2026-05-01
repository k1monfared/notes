// Inline editor overlay for the static movies viewer.
//
// Activates when the user clicks the lock button and connects a GitHub
// token. In edit mode, every movie card grows a pencil button; clicking
// it opens a modal with the editable fields. Save commits the modified
// movies.log via the GitHub API and triggers the viewer to re-render.
//
// All heavy lifting (parser, route, mutation helpers, GitHub API) is
// borrowed from the existing movie-writer/js/ modules so we don't
// duplicate logic.

import {
  parseMovies, findMovie, findInsertAfter,
  setStatus, setReview, setProperty, removeProperty, setNotes,
  buildMovieEntry, findToWatchInsert,
} from '../movie-writer/js/movies.js';
import { autoRoute, applyMove } from '../movie-writer/js/route.js';
import { createCommit, getFile } from '../movie-writer/js/github.js';
import {
  isAuthenticated, getToken, setToken, clearToken, validateToken,
} from '../movie-writer/js/auth.js';

const REPO = 'k1monfared/notes';
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

// ── State ────────────────────────────────────────────────────────────────────

let saving = false;

// ── Helpers ──────────────────────────────────────────────────────────────────

function splitLines(text) {
  return text.split('\n').map((l, i, a) => i < a.length - 1 ? l + '\n' : (l ? l + '\n' : ''));
}

function joinLines(lines) {
  return lines.join('').replace(/\n$/, '');
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
}

function findEntryByTitle(text, title) {
  const parsed = parseMovies(text);
  return parsed.movies.find(m => m.title === title) || null;
}

// ── Edit-mode toggle ─────────────────────────────────────────────────────────

function applyEditMode() {
  document.body.classList.toggle('edit-mode', isAuthenticated());
}

function setupLockButton() {
  const btn = document.getElementById('edit-lock');
  if (!btn) return;
  applyEditMode();
  btn.title = isAuthenticated() ? 'Disconnect from edit mode' : 'Sign in to edit';
  btn.addEventListener('click', () => {
    if (isAuthenticated()) {
      if (confirm('Disconnect from edit mode?')) {
        clearToken();
        applyEditMode();
        btn.title = 'Sign in to edit';
        location.reload();
      }
    } else {
      showLoginDialog();
    }
  });
}

function showLoginDialog() {
  const overlay = document.createElement('div');
  overlay.className = 'editor-dialog-overlay';
  overlay.innerHTML = `
    <div class="editor-dialog">
      <h3>Connect to GitHub</h3>
      <p class="dialog-hint">Paste a fine-grained Personal Access Token for <code>${REPO}</code>
      with <strong>Contents read/write</strong> permission.
      <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">Create one</a>.</p>
      <input type="password" id="login-token" placeholder="github_pat_..." autocomplete="off">
      <div class="dialog-error" id="login-error"></div>
      <div class="dialog-actions">
        <button class="btn-cancel">Cancel</button>
        <button class="btn-primary" id="login-connect">Connect</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  const input = overlay.querySelector('#login-token');
  const errEl = overlay.querySelector('#login-error');
  const connect = overlay.querySelector('#login-connect');
  input.focus();
  const close = () => overlay.remove();
  overlay.querySelector('.btn-cancel').addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function onEsc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onEsc); }
  });
  connect.addEventListener('click', async () => {
    const token = input.value.trim();
    if (!token) { errEl.textContent = 'Please enter a token.'; return; }
    connect.disabled = true; connect.textContent = 'Validating…';
    const result = await validateToken(token);
    if (result.valid) {
      setToken(token);
      close();
      applyEditMode();
      const lockBtn = document.getElementById('edit-lock');
      if (lockBtn) lockBtn.title = 'Disconnect from edit mode';
      showToast('Edit mode active');
    } else {
      errEl.textContent = result.error;
      connect.disabled = false; connect.textContent = 'Connect';
    }
  });
  input.addEventListener('keydown', e => { if (e.key === 'Enter') connect.click(); });
}

// ── Pencil click delegation ─────────────────────────────────────────────────

// Use capture phase so we run BEFORE the inline onclick on .mv-hdr
// (toggleMv) which would otherwise fold the card on pencil click.
document.addEventListener('click', (e) => {
  const editBtn = e.target.closest('[data-action="edit-movie"]');
  if (editBtn) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    const card = editBtn.closest('.mv');
    if (!card) return;
    const title = card.querySelector('.mv-name')?.textContent.trim();
    if (title) openEditDialog(title);
    return;
  }
  const searchAddBtn = e.target.closest('[data-action="search-add"]');
  if (searchAddBtn) {
    e.preventDefault();
    e.stopPropagation();
    openAddDialog(searchAddBtn.dataset.title || '');
  }
}, true);

// ── Edit dialog ──────────────────────────────────────────────────────────────

function openEditDialog(title) {
  const text = window.__moviesText;
  if (!text) { showToast('No data loaded yet', 'error'); return; }
  const entry = findEntryByTitle(text, title);
  if (!entry) { showToast(`"${title}" not found`, 'error'); return; }

  const p = entry.props;
  const isInWatched = (entry.section || '').toLowerCase() === 'watched';
  const currentCategory = isInWatched ? entry.category : '';
  const overlay = document.createElement('div');
  overlay.className = 'editor-dialog-overlay';
  overlay.innerHTML = `
    <div class="editor-dialog editor-dialog-wide">
      <h3>Edit movie</h3>
      <div class="dialog-grid">
        <label>Title</label>
        <input type="text" id="ed-title" value="${esc(entry.title)}">

        <label>Status</label>
        <select id="ed-status">
          <option value="" ${entry.status === '' ? 'selected' : ''}>unwatched</option>
          <option value="x" ${entry.status === 'x' ? 'selected' : ''}>watched</option>
          <option value="-" ${entry.status === '-' ? 'selected' : ''}>skipped</option>
          <option value="?" ${entry.status === '?' ? 'selected' : ''}>uncertain</option>
        </select>

        <label>Category</label>
        <select id="ed-category">
          <option value="" ${!currentCategory ? 'selected' : ''}>(none)</option>
          ${RATED_CATEGORIES.map(c => `<option value="${esc(c)}" ${currentCategory === c ? 'selected' : ''}>${esc(c)}</option>`).join('')}
        </select>

        <label>Recommender</label>
        <input type="text" id="ed-recommender" value="${esc(p.recommender || '')}">

        <label>Year</label>
        <input type="text" id="ed-year" value="${esc(p.year || '')}">

        <label>Director</label>
        <input type="text" id="ed-director" value="${esc(p.director || '')}">

        <label>IMDb URL</label>
        <input type="text" id="ed-imdb" value="${esc(p.imdb || '')}">

        <label>Tags</label>
        <input type="text" id="ed-tags" placeholder="comma,separated" value="${esc((p.tags || (p.tag ? [p.tag] : [])).join(', '))}">

        <label>Review</label>
        <textarea id="ed-review" rows="4">${esc(p.review || '')}</textarea>

        <label>Notes</label>
        <textarea id="ed-notes" rows="4" placeholder="Free-form notes, one per line">${esc((p.notes || []).join('\n'))}</textarea>
      </div>
      <div class="dialog-error" id="ed-error"></div>
      <div class="dialog-actions">
        <button class="btn-danger" id="ed-delete">Delete</button>
        <button class="btn-secondary" id="ed-fetch-imdb">Fetch IMDb info</button>
        <span style="flex:1"></span>
        <button class="btn-cancel" id="ed-cancel">Cancel</button>
        <button class="btn-primary" id="ed-save">Save</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const close = () => overlay.remove();
  overlay.querySelector('#ed-cancel').addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function onEsc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onEsc); }
  });

  overlay.querySelector('#ed-fetch-imdb').addEventListener('click', async () => {
    const fetchBtn = overlay.querySelector('#ed-fetch-imdb');
    fetchBtn.disabled = true; fetchBtn.textContent = 'Searching…';
    const titleNow = overlay.querySelector('#ed-title').value.trim() || entry.title;
    const yearNow  = overlay.querySelector('#ed-year').value.trim() || p.year || '';
    const result = await showImdbPicker(titleNow, yearNow);
    if (result) {
      try {
        await applyImdbDetails(entry.title, result);
        close();
        return;
      } catch (err) {
        overlay.querySelector('#ed-error').textContent = 'Apply failed: ' + err.message;
      }
    }
    fetchBtn.disabled = false; fetchBtn.textContent = 'Fetch IMDb info';
  });

  overlay.querySelector('#ed-save').addEventListener('click', async () => {
    if (saving) return;
    const errEl = overlay.querySelector('#ed-error');
    const newTitle = overlay.querySelector('#ed-title').value.trim();
    if (!newTitle) { errEl.textContent = 'Title is required.'; return; }

    const updates = {
      title: newTitle,
      status: overlay.querySelector('#ed-status').value,
      category: overlay.querySelector('#ed-category').value,
      recommender: overlay.querySelector('#ed-recommender').value.trim(),
      year: overlay.querySelector('#ed-year').value.trim(),
      director: overlay.querySelector('#ed-director').value.trim(),
      imdb: overlay.querySelector('#ed-imdb').value.trim(),
      tags: overlay.querySelector('#ed-tags').value.trim(),
      review: overlay.querySelector('#ed-review').value.trim(),
      notes: overlay.querySelector('#ed-notes').value.split('\n').map(s => s.trim()).filter(Boolean),
    };

    overlay.querySelector('#ed-save').disabled = true;
    overlay.querySelector('#ed-save').textContent = 'Saving…';
    try {
      await commitEdit(entry.title, updates);
      close();
    } catch (err) {
      errEl.textContent = 'Save failed: ' + err.message;
      overlay.querySelector('#ed-save').disabled = false;
      overlay.querySelector('#ed-save').textContent = 'Save';
    }
  });

  overlay.querySelector('#ed-delete').addEventListener('click', async () => {
    if (saving) return;
    if (!confirm(`Delete "${entry.title}" from movies.log?`)) return;
    overlay.querySelector('#ed-delete').disabled = true;
    overlay.querySelector('#ed-delete').textContent = 'Deleting…';
    try {
      await commitDelete(entry.title);
      close();
    } catch (err) {
      overlay.querySelector('#ed-error').textContent = 'Delete failed: ' + err.message;
      overlay.querySelector('#ed-delete').disabled = false;
      overlay.querySelector('#ed-delete').textContent = 'Delete';
    }
  });
}

// ── Mutation + commit ────────────────────────────────────────────────────────

async function commitEdit(originalTitle, u) {
  saving = true;
  try {
    const text = window.__moviesText;
    let lines = splitLines(text);

    // Locate the entry
    let found = findMovie(lines, originalTitle);
    if (!found) throw new Error(`"${originalTitle}" not found in file`);

    // 1. Title rename
    if (u.title !== originalTitle) {
      lines[found.index] = lines[found.index].replace(originalTitle, u.title);
      found = findMovie(lines, u.title);
      if (!found) throw new Error('Title rename failed');
    }

    // 2. Status flip
    setStatus(lines, found.index, u.status);

    // 3. Property updates
    const setOrRemove = (key, val) => {
      if (val) setProperty(lines, found.index, found.indent, key, val);
      else removeProperty(lines, found.index, found.indent, key);
    };
    setOrRemove('Recommender', u.recommender);
    setOrRemove('Year', u.year);
    setOrRemove('Director', u.director);
    setOrRemove('IMDB', u.imdb);
    setOrRemove('tag', u.tags);
    if (u.review) setReview(lines, found.index, found.indent, u.review);
    else removeProperty(lines, found.index, found.indent, 'review');
    // Replace all "note" lines under this entry with the user's textarea
    setNotes(lines, found.index, found.indent, u.notes || []);

    // 4. Category move (if explicit category chosen, move into watched > <category>)
    if (u.category) {
      const reparsed = parseMovies(joinLines(lines));
      const entry = reparsed.movies.find(m => m.title === u.title);
      if (entry) {
        const movedLines = applyMove(lines, entry, 'watched', u.category);
        if (movedLines) lines = movedLines;
      }
    } else {
      // No explicit category — let auto-route place based on status + review
      const reparsed = parseMovies(joinLines(lines));
      const entry = reparsed.movies.find(m => m.title === u.title);
      if (entry) {
        const routed = autoRoute(lines, entry);
        if (routed) lines = routed.lines;
      }
    }

    const newText = joinLines(lines);
    await pushAndRefresh(newText, `Edit ${u.title}`);
    showToast(`Saved ${u.title}`);
  } finally {
    saving = false;
  }
}

async function commitDelete(title) {
  saving = true;
  try {
    const text = window.__moviesText;
    const lines = splitLines(text);
    const found = findMovie(lines, title);
    if (!found) throw new Error('Not found');
    const end = findInsertAfter(lines, found.index, found.indent);
    lines.splice(found.index, end - found.index);
    await pushAndRefresh(joinLines(lines), `Delete ${title}`);
    showToast(`Deleted ${title}`);
  } finally {
    saving = false;
  }
}

async function commitAdd(payload, forceDuplicate = false) {
  saving = true;
  try {
    const text = window.__moviesText;
    const lines = splitLines(text);
    if (!forceDuplicate && findMovie(lines, payload.title)) {
      throw new Error(`"${payload.title}" already exists`);
    }

    const insert = findToWatchInsert(lines, payload.recommender || null);
    if (!insert) throw new Error('Could not find an insertion point in To Watch');
    let i = insert.index;
    if (insert.newLines) for (const nl of insert.newLines) lines.splice(i++, 0, nl);
    const block = buildMovieEntry(payload.title, payload, insert.indent);
    lines.splice(i, 0, ...block);

    await pushAndRefresh(joinLines(lines), `Add ${payload.title}`);
    showToast(`Added ${payload.title}`);
  } finally {
    saving = false;
  }
}

async function pushAndRefresh(newText, message) {
  await createCommit([{ path: 'movies.log', content: newText }], message);
  // Show the local result immediately so the user sees their edit.
  await window.__refreshMoviesText(newText);

  // The enrich + cleanup workflow runs after every push. Poll the file
  // until its content differs from what we just pushed (i.e. the workflow
  // has committed enrichment + dedupe + route + key-normalisation on top),
  // then refresh the viewer with that post-pipeline version.
  pollForEnrichment(newText).catch(err => {
    console.warn('post-save refresh failed:', err);
  });
}

async function pollForEnrichment(ourText, attempts = 0) {
  // Wait up to ~90 seconds (15 polls × 6s) for the enrichment workflow
  // to commit on top of ours.
  if (attempts >= 15) return;
  await new Promise(r => setTimeout(r, 6000));
  try {
    const file = await getFile('movies.log');
    if (file.content !== ourText && file.content !== window.__moviesText) {
      // The workflow committed a newer version. Pull it in.
      await window.__refreshMoviesText(file.content);
      showToast('Enrichment + cleanup applied');
      return;
    }
  } catch { /* transient — keep polling */ }
  return pollForEnrichment(ourText, attempts + 1);
}

// ── Add modal ────────────────────────────────────────────────────────────────

function openAddDialog(prefillTitle = '') {
  const overlay = document.createElement('div');
  overlay.className = 'editor-dialog-overlay';
  overlay.innerHTML = `
    <div class="editor-dialog">
      <h3>Add movie</h3>
      <div class="dialog-grid">
        <label>Title *</label>
        <input type="text" id="add-title" autofocus value="${esc(prefillTitle)}">

        <label>Recommender</label>
        <input type="text" id="add-rec">

        <label>Director</label>
        <input type="text" id="add-director">

        <label>Year</label>
        <input type="text" id="add-year">

        <label>Review</label>
        <textarea id="add-review" rows="3"></textarea>
      </div>
      <div class="dialog-error" id="add-error"></div>
      <div class="dialog-actions">
        <button class="btn-cancel">Cancel</button>
        <button class="btn-primary" id="add-save">Add</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  overlay.querySelector('.btn-cancel').addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function onEsc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onEsc); }
  });
  overlay.querySelector('#add-save').addEventListener('click', async () => {
    if (saving) return;
    const errEl = overlay.querySelector('#add-error');
    const title = overlay.querySelector('#add-title').value.trim();
    if (!title) { errEl.textContent = 'Title is required.'; return; }
    const payload = {
      title,
      recommender: overlay.querySelector('#add-rec').value.trim(),
      director: overlay.querySelector('#add-director').value.trim(),
      year: overlay.querySelector('#add-year').value.trim(),
      review: overlay.querySelector('#add-review').value.trim(),
    };

    // Duplicate detection: case-insensitive title match against the parsed file
    const existing = findEntryByTitle(window.__moviesText, title)
      || findEntryByTitleCi(window.__moviesText, title);
    if (existing) {
      const choice = await showDuplicateDialog(existing);
      if (choice === 'cancel') return;
      if (choice === 'edit-existing') {
        close();
        openEditDialog(existing.title);
        return;
      }
      // 'add-anyway' → fall through
    }

    overlay.querySelector('#add-save').disabled = true;
    overlay.querySelector('#add-save').textContent = 'Adding…';
    try {
      await commitAdd(payload, /* forceDuplicate */ !!existing);
      close();
    } catch (err) {
      errEl.textContent = 'Add failed: ' + err.message;
      overlay.querySelector('#add-save').disabled = false;
      overlay.querySelector('#add-save').textContent = 'Add';
    }
  });
}

function findEntryByTitleCi(text, title) {
  const titleLc = title.toLowerCase();
  const parsed = parseMovies(text);
  return parsed.movies.find(m => m.title.toLowerCase() === titleLc) || null;
}

// ── OMDb integration (browser-side, opt-in per click) ───────────────────────

const OMDB_KEY = 'omdb_api_key';
const getOmdbKey = () => localStorage.getItem(OMDB_KEY);
const setOmdbKey = (k) => localStorage.setItem(OMDB_KEY, k.trim());

async function ensureOmdbKey() {
  let k = getOmdbKey();
  if (k) return k;
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'editor-dialog-overlay';
    overlay.innerHTML = `
      <div class="editor-dialog">
        <h3>OMDb API key</h3>
        <p class="dialog-hint">Paste your OMDb API key (free at
        <a href="https://www.omdbapi.com/apikey.aspx" target="_blank" rel="noopener">omdbapi.com/apikey.aspx</a>).
        Stored in localStorage; only sent to omdbapi.com.</p>
        <input type="password" id="omdb-key" placeholder="1234abcd" autocomplete="off">
        <div class="dialog-actions">
          <button class="btn-cancel">Cancel</button>
          <button class="btn-primary" id="omdb-save">Save</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const input = overlay.querySelector('#omdb-key');
    input.focus();
    const done = (val) => { overlay.remove(); resolve(val); };
    overlay.querySelector('.btn-cancel').addEventListener('click', () => done(null));
    overlay.querySelector('#omdb-save').addEventListener('click', () => {
      const v = input.value.trim();
      if (!v) return;
      setOmdbKey(v);
      done(v);
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') overlay.querySelector('#omdb-save').click(); });
    overlay.addEventListener('click', e => { if (e.target === overlay) done(null); });
  });
}

async function omdbSearch(title, year) {
  const key = await ensureOmdbKey();
  if (!key) throw new Error('OMDb key not provided');
  const params = new URLSearchParams({ apikey: key, s: title, type: 'movie' });
  if (year) params.set('y', year);
  const res = await fetch(`https://www.omdbapi.com/?${params}`);
  const data = await res.json();
  if (data.Response === 'False') return [];
  return data.Search || [];
}

async function omdbDetails(imdbID) {
  const key = await ensureOmdbKey();
  if (!key) throw new Error('OMDb key not provided');
  const params = new URLSearchParams({ apikey: key, i: imdbID, plot: 'short' });
  const res = await fetch(`https://www.omdbapi.com/?${params}`);
  const data = await res.json();
  if (data.Response === 'False') return null;
  return data;
}

// Build IMDb property lines for an entry (mirrors scripts/enrich_all.py
// build_imdb_lines but without the "(IMDb)" suffix since cleanup strips it).
function buildImdbPropertyLines(d, indent) {
  const pad = ' '.repeat(indent + 4);
  const deepPad = ' '.repeat(indent + 8);
  const na = (v) => (v && v !== 'N/A') ? v : null;
  const out = [];
  const fields = [
    ['Year',         na(d.Year)],
    ['IMDB Rating',  na(d.imdbRating) ? `${d.imdbRating}/10` : null],
    ['Genres',       na(d.Genre)],
    ['Country',      na(d.Country)],
    ['Duration',     na(d.Runtime)],
    ['Released',     na(d.Released)],
    ['Director',     na(d.Director)],
    ['Synopsis',     na(d.Plot)],
  ];
  for (const [k, v] of fields) if (v) out.push(`${pad}- ${k}: ${v}\n`);
  const actors = na(d.Actors);
  if (actors) {
    out.push(`${pad}- Cast:\n`);
    for (const a of actors.split(',').slice(0, 5)) out.push(`${deepPad}- ${a.trim()}\n`);
  }
  if (d.imdbID) out.push(`${pad}- IMDB: https://www.imdb.com/title/${d.imdbID}/\n`);
  return out;
}

// Open a picker, fetch candidates, let user choose / mark N/A / cancel.
async function showImdbPicker(title, hintYear) {
  let candidates;
  try {
    candidates = await omdbSearch(title, hintYear);
    if (!candidates.length && hintYear) {
      // Retry without year filter — handles wrong/missing year
      candidates = await omdbSearch(title);
    }
  } catch (err) {
    showToast('OMDb search failed: ' + err.message, 'error');
    return null;
  }

  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'editor-dialog-overlay';
    const list = candidates.length
      ? candidates.slice(0, 8).map(r => `
        <button class="imdb-candidate" data-id="${esc(r.imdbID)}">
          ${r.Poster && r.Poster !== 'N/A' ? `<img src="${esc(r.Poster)}" alt="">` : '<span class="poster-placeholder">🎬</span>'}
          <div class="cand-meta">
            <div class="cand-title">${esc(r.Title)}</div>
            <div class="cand-sub">${esc(r.Year || '')} · ${esc(r.Type || '')}</div>
          </div>
        </button>`).join('')
      : '<p class="dialog-hint">No matches in OMDb.</p>';
    overlay.innerHTML = `
      <div class="editor-dialog editor-dialog-wide">
        <h3>Pick IMDb match for "${esc(title)}"${hintYear ? ' (' + esc(hintYear) + ')' : ''}</h3>
        <div class="imdb-candidates">${list}</div>
        <div class="dialog-actions">
          <button class="btn-cancel">Cancel</button>
          <span style="flex:1"></span>
          <button class="btn-secondary" id="imdb-na">None of these (mark N/A)</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = (result) => { overlay.remove(); resolve(result); };
    overlay.querySelector('.btn-cancel').addEventListener('click', () => close(null));
    overlay.querySelector('#imdb-na').addEventListener('click', () => close({ na: true }));
    overlay.addEventListener('click', e => { if (e.target === overlay) close(null); });
    overlay.querySelectorAll('.imdb-candidate').forEach(b => {
      b.addEventListener('click', async () => {
        const id = b.dataset.id;
        b.classList.add('selected');
        b.disabled = true;
        try {
          const d = await omdbDetails(id);
          close(d);
        } catch (err) {
          showToast('Detail fetch failed: ' + err.message, 'error');
          b.disabled = false;
          b.classList.remove('selected');
        }
      });
    });
  });
}

// Apply IMDb data to an entry: replace existing IMDb-related properties,
// then commit.
async function applyImdbDetails(originalTitle, details) {
  const text = window.__moviesText;
  const lines = splitLines(text);
  const found = findMovie(lines, originalTitle);
  if (!found) throw new Error('Not found');
  // Remove any existing IMDb fields (so re-pick replaces them cleanly)
  for (const k of ['Year', 'IMDB Rating', 'Genres', 'Country', 'Duration', 'Released', 'Director', 'Synopsis', 'IMDB', 'Cast']) {
    removeProperty(lines, found.index, found.indent, k);
  }
  if (details.na) {
    setProperty(lines, found.index, found.indent, 'IMDB', 'N/A');
    await pushAndRefresh(joinLines(lines), `${originalTitle}: mark IMDb N/A`);
    showToast(`${originalTitle}: marked N/A`);
    return;
  }
  const newProps = buildImdbPropertyLines(details, found.indent);
  const insertAt = findInsertAfter(lines, found.index, found.indent);
  lines.splice(insertAt, 0, ...newProps);
  await pushAndRefresh(joinLines(lines), `Enrich ${originalTitle} from IMDb`);
  showToast(`${originalTitle}: IMDb data applied`);
}

// ── Duplicate detection on Add ───────────────────────────────────────────────

function previewExistingEntry(entry) {
  const p = entry.props;
  // Each row is [label, escapedValueHTML].
  const rows = [];
  if (entry.section || entry.category) {
    const path = [entry.section, entry.category, entry.subsection].filter(Boolean).join(' › ');
    rows.push(['Section', esc(path)]);
  }
  if (p.year)        rows.push(['Year', esc(p.year)]);
  if (p.director)    rows.push(['Director', esc(p.director)]);
  if (p.recommender) rows.push(['Recommender', esc(p.recommender)]);
  if (p.review) {
    const r = p.review.length > 120 ? p.review.slice(0, 120) + '…' : p.review;
    rows.push(['Review', esc(r)]);
  }
  // Always show the IMDb link last if we have one
  if (p.imdb) {
    if (p.imdb.startsWith('http')) {
      rows.push(['IMDb', `<a href="${esc(p.imdb)}" target="_blank" rel="noopener">${esc(p.imdb)}</a>`]);
    } else {
      rows.push(['IMDb', esc(p.imdb)]);
    }
  }
  return rows.map(([k, v]) => `<div class="dup-row"><strong>${esc(k)}</strong> ${v}</div>`).join('');
}

function showDuplicateDialog(existing) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'editor-dialog-overlay';
    overlay.innerHTML = `
      <div class="editor-dialog">
        <h3>"${esc(existing.title)}" already exists</h3>
        <div class="dup-preview">${previewExistingEntry(existing)}</div>
        <div class="dialog-actions">
          <button class="btn-cancel" data-act="cancel">Cancel</button>
          <span style="flex:1"></span>
          <button class="btn-secondary" data-act="add-anyway">Add anyway</button>
          <button class="btn-primary" data-act="edit-existing">Edit existing</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const done = (v) => { overlay.remove(); resolve(v); };
    overlay.querySelectorAll('button[data-act]').forEach(b =>
      b.addEventListener('click', () => done(b.dataset.act))
    );
    overlay.addEventListener('click', e => { if (e.target === overlay) done('cancel'); });
  });
}

// ── Toast ────────────────────────────────────────────────────────────────────

let toastEl = null;
let toastTimer = null;

function showToast(msg, type = 'info') {
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.className = 'editor-toast';
    document.body.appendChild(toastEl);
  }
  clearTimeout(toastTimer);
  toastEl.textContent = msg;
  toastEl.className = `editor-toast toast-${type} visible`;
  if (type !== 'error') {
    toastTimer = setTimeout(() => toastEl.classList.remove('visible'), 2500);
  }
  toastEl.onclick = () => toastEl.classList.remove('visible');
}

// ── Add a "+ New movie" button next to the lock ──────────────────────────────

function setupAddButton() {
  const lock = document.getElementById('edit-lock');
  if (!lock || document.getElementById('add-movie-btn')) return;
  const btn = document.createElement('button');
  btn.id = 'add-movie-btn';
  btn.className = 'hdr-icon-btn edit-only';
  btn.title = 'Add a new movie';
  btn.setAttribute('aria-label', 'Add movie');
  btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
  lock.parentNode.insertBefore(btn, lock);
  btn.addEventListener('click', openAddDialog);
}

// ── Boot ─────────────────────────────────────────────────────────────────────

setupLockButton();
setupAddButton();
