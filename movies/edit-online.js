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
  setStatus, setReview, setProperty, removeProperty,
  buildMovieEntry, findToWatchInsert,
} from '../movie-writer/js/movies.js';
import { autoRoute, applyMove } from '../movie-writer/js/route.js';
import { createCommit } from '../movie-writer/js/github.js';
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

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action="edit-movie"]');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  const card = btn.closest('.mv');
  if (!card) return;
  const title = card.querySelector('.mv-name')?.textContent.trim();
  if (!title) return;
  openEditDialog(title);
});

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
      </div>
      <div class="dialog-error" id="ed-error"></div>
      <div class="dialog-actions">
        <button class="btn-danger" id="ed-delete">Delete</button>
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

async function commitAdd(payload) {
  saving = true;
  try {
    const text = window.__moviesText;
    const lines = splitLines(text);
    if (findMovie(lines, payload.title)) throw new Error(`"${payload.title}" already exists`);

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
  await window.__refreshMoviesText(newText);
}

// ── Add modal ────────────────────────────────────────────────────────────────

function openAddDialog() {
  const overlay = document.createElement('div');
  overlay.className = 'editor-dialog-overlay';
  overlay.innerHTML = `
    <div class="editor-dialog">
      <h3>Add movie</h3>
      <div class="dialog-grid">
        <label>Title *</label>
        <input type="text" id="add-title" autofocus>

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
    overlay.querySelector('#add-save').disabled = true;
    overlay.querySelector('#add-save').textContent = 'Adding…';
    try {
      await commitAdd(payload);
      close();
    } catch (err) {
      errEl.textContent = 'Add failed: ' + err.message;
      overlay.querySelector('#add-save').disabled = false;
      overlay.querySelector('#add-save').textContent = 'Add';
    }
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
