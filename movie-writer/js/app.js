// Movie Writer PWA - Local-first with background sync

import { isAuthenticated, getToken, setToken, clearToken, validateToken } from './auth.js';
import { getFile, createCommit } from './github.js';
import {
  getLocalMovies, setLocalMovies,
  isDirty, setDirty,
  addPendingMessage, getPendingMessages, clearPendingMessages,
} from './storage.js';
import {
  parseMovies, findMovie, findInsertAfter, findToWatchInsert,
  buildMovieEntry, markWatched, setReview, setProperty,
} from './movies.js';

const app = document.getElementById('app');
let moviesText = null;  // current local text
let moviesList = null;  // parsed from moviesText
let syncInProgress = false;

// ── Helpers ──────────────────────────────────────────────────────────────────

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function splitLines(text) {
  // Split into lines preserving newlines for modification
  return text.split('\n').map((l, i, arr) => i < arr.length - 1 ? l + '\n' : (l ? l + '\n' : ''));
}

function joinLines(lines) {
  return lines.join('').replace(/\n$/, '');
}

// ── Local State ──────────────────────────────────────────────────────────────

async function loadLocal() {
  moviesText = await getLocalMovies();
  if (moviesText) {
    moviesList = parseMovies(moviesText);
    return true;
  }
  return false;
}

async function saveLocal(text, commitMessage) {
  moviesText = text;
  moviesList = parseMovies(text);
  await setLocalMovies(text);
  await setDirty(true);
  await addPendingMessage(commitMessage);
  updateSyncBadge();
  triggerSync();
}

async function fetchFromGitHub() {
  const file = await getFile('movies.log');
  moviesText = file.content;
  moviesList = parseMovies(moviesText);
  // Only overwrite local if not dirty (don't lose unpushed changes)
  const dirty = await isDirty();
  if (!dirty) {
    await setLocalMovies(moviesText);
  }
  return true;
}

// ── Background Sync ──────────────────────────────────────────────────────────

let syncTimeout = null;

function triggerSync() {
  if (syncTimeout) clearTimeout(syncTimeout);
  // Small delay to batch rapid changes
  syncTimeout = setTimeout(() => doSync(), 1500);
}

async function doSync() {
  if (syncInProgress) return;
  const dirty = await isDirty();
  if (!dirty || !moviesText) return;

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
  } catch (err) {
    console.error('Sync failed:', err);
    // Will retry on next triggerSync or app focus
  } finally {
    syncInProgress = false;
    updateSyncBadge();
  }
}

function updateSyncBadge() {
  const badge = document.getElementById('sync-badge');
  if (!badge) return;
  if (syncInProgress) {
    badge.textContent = 'syncing...';
    badge.className = 'sync-badge syncing';
  } else {
    isDirty().then(dirty => {
      if (!badge.isConnected) return;
      if (dirty) {
        badge.textContent = 'pending';
        badge.className = 'sync-badge pending';
      } else {
        badge.textContent = 'synced';
        badge.className = 'sync-badge synced';
      }
    });
  }
}

// Retry sync on app focus
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && isAuthenticated()) {
    isDirty().then(dirty => { if (dirty) triggerSync(); });
  }
});

// ── Setup Screen ─────────────────────────────────────────────────────────────

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
    btn.disabled = true;
    btn.textContent = 'Validating...';
    const result = await validateToken(token);
    if (result.valid) {
      setToken(token);
      showMovieList();
    } else {
      errEl.textContent = result.error;
      errEl.hidden = false;
      btn.disabled = false;
      btn.textContent = 'Connect';
    }
  });
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') btn.click(); });
}

// ── Movie List Screen ────────────────────────────────────────────────────────

async function showMovieList(forceRefresh = false) {
  app.innerHTML = `
    <div class="screen list-screen">
      <header class="app-header">
        <h1>Movies</h1>
        <div class="header-actions">
          <span id="sync-badge" class="sync-badge"></span>
          <button id="refresh-btn" class="btn icon" title="Pull from GitHub">&#8635;</button>
          <button id="settings-btn" class="btn icon" title="Settings">&#9881;</button>
        </div>
      </header>
      <div class="tabs">
        <button class="tab active" data-tab="to_watch">To Watch</button>
        <button class="tab" data-tab="watched">Watched</button>
      </div>
      <div class="search-bar">
        <input type="text" id="search-input" placeholder="Search movies...">
      </div>
      <button id="add-btn" class="btn primary full-width">+ Add Movie</button>
      <div id="movie-list" class="movie-list">
        <div class="loading">Loading movies...</div>
      </div>
    </div>
  `;

  app.querySelector('#add-btn').addEventListener('click', () => showAddEdit());
  app.querySelector('#refresh-btn').addEventListener('click', async () => {
    const listEl = app.querySelector('#movie-list');
    if (listEl) listEl.innerHTML = '<div class="loading">Pulling from GitHub...</div>';
    try {
      await fetchFromGitHub();
      await setLocalMovies(moviesText);
    } catch (err) {
      if (listEl) listEl.innerHTML = `<div class="error">Pull failed: ${esc(err.message)}</div>`;
      return;
    }
    renderList();
  });
  app.querySelector('#settings-btn').addEventListener('click', showSettings);

  // Tabs
  let activeTab = 'to_watch';
  app.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      app.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeTab = tab.dataset.tab;
      renderList();
    });
  });

  // Search
  const searchInput = app.querySelector('#search-input');
  searchInput.addEventListener('input', () => renderList());

  function renderList() {
    const listEl = app.querySelector('#movie-list');
    if (!listEl || !moviesList) return;

    const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
    let filtered = moviesList.filter(m => m.section === activeTab);
    if (query) {
      filtered = filtered.filter(m =>
        m.title.toLowerCase().includes(query) ||
        (m.director || '').toLowerCase().includes(query) ||
        (m.recommender || '').toLowerCase().includes(query) ||
        (m.genres || '').toLowerCase().includes(query) ||
        (m.review || '').toLowerCase().includes(query)
      );
    }

    if (filtered.length === 0) {
      listEl.innerHTML = `<p class="empty">${query ? 'No matches' : 'No movies in this section'}</p>`;
      return;
    }

    listEl.innerHTML = filtered.map((m, i) => `
      <div class="movie-card" data-idx="${i}">
        <div class="movie-header">
          <span class="movie-status">${m.watched ? '&#9745;' : '&#9744;'}</span>
          <div class="movie-info">
            <div class="movie-title">${esc(m.title)}</div>
            <div class="movie-meta">
              ${m.director ? esc(m.director) : ''}${m.year ? ' (' + esc(m.year) + ')' : ''}${m.rating ? ' &middot; ' + esc(m.rating) : ''}${m.recommender ? ' &middot; via ' + esc(m.recommender) : ''}
            </div>
          </div>
          <span class="expand-icon">&#9660;</span>
        </div>
        <div class="movie-details" hidden>
          ${m.genres ? `<div class="detail-row"><strong>Genres:</strong> ${esc(m.genres)}</div>` : ''}
          ${m.country ? `<div class="detail-row"><strong>Country:</strong> ${esc(m.country)}</div>` : ''}
          ${m.duration ? `<div class="detail-row"><strong>Duration:</strong> ${esc(m.duration)}</div>` : ''}
          ${m.synopsis ? `<div class="detail-row"><strong>Synopsis:</strong> ${esc(m.synopsis)}</div>` : ''}
          ${m.cast ? `<div class="detail-row"><strong>Cast:</strong> ${esc(m.cast.join(', '))}</div>` : ''}
          ${m.review ? `<div class="detail-row review"><strong>Review:</strong> ${esc(m.review)}</div>` : ''}
          ${m.notes ? `<div class="detail-row"><strong>Notes:</strong> ${esc(m.notes)}</div>` : ''}
          ${m.imdb ? `<div class="detail-row"><a href="${esc(m.imdb)}" target="_blank" rel="noopener">IMDb</a></div>` : ''}
          <div class="movie-actions">
            ${!m.watched ? `<button class="btn small action-watched" data-title="${esc(m.title)}">Mark Watched</button>` : `<button class="btn small action-unwatched" data-title="${esc(m.title)}">Mark Unwatched</button>`}
            <button class="btn small action-review" data-title="${esc(m.title)}">Add Review</button>
            <button class="btn small action-edit" data-title="${esc(m.title)}">Edit</button>
          </div>
        </div>
      </div>
    `).join('');

    listEl.querySelectorAll('.movie-header').forEach(header => {
      header.addEventListener('click', () => {
        const details = header.nextElementSibling;
        const icon = header.querySelector('.expand-icon');
        details.hidden = !details.hidden;
        icon.innerHTML = details.hidden ? '&#9660;' : '&#9650;';
      });
    });

    listEl.querySelectorAll('.action-watched').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); doMarkWatched(btn.dataset.title); });
    });
    listEl.querySelectorAll('.action-unwatched').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); doMarkUnwatched(btn.dataset.title); });
    });
    listEl.querySelectorAll('.action-review').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); showReviewDialog(btn.dataset.title); });
    });
    listEl.querySelectorAll('.action-edit').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); showAddEdit(btn.dataset.title); });
    });
  }

  // Load data: local first, then GitHub if needed
  const hasLocal = await loadLocal();
  if (hasLocal && !forceRefresh) {
    renderList();
    updateSyncBadge();
    return;
  }

  // No local data: fetch from GitHub
  try {
    await fetchFromGitHub();
    await setLocalMovies(moviesText);
    renderList();
    updateSyncBadge();
  } catch (err) {
    const listEl = app.querySelector('#movie-list');
    if (listEl) listEl.innerHTML = `<div class="error">Failed to load: ${esc(err.message)}</div>`;
  }
}

// ── Local mutations (instant, no waiting for GitHub) ─────────────────────────

function mutateLocal(mutateFn, commitMessage) {
  let lines = splitLines(moviesText);
  lines = mutateFn(lines);
  const newText = joinLines(lines);
  saveLocal(newText, commitMessage);
}

async function doMarkWatched(title) {
  const review = prompt('Add a review? (optional, press Cancel to skip)');

  mutateLocal((lines) => {
    const found = findMovie(lines, title);
    if (!found) { alert(`"${title}" not found`); return lines; }
    markWatched(lines, found.index);
    if (review) setReview(lines, found.index, found.indent, review);
    return lines;
  }, `Mark watched: ${title}`);

  showMovieList();
}

async function doMarkUnwatched(title) {
  mutateLocal((lines) => {
    const found = findMovie(lines, title);
    if (!found) { alert(`"${title}" not found`); return lines; }
    lines[found.index] = lines[found.index].replace(/\[[x\-? ]?\]/i, '[]');
    return lines;
  }, `Mark unwatched: ${title}`);

  showMovieList();
}

// ── Review Dialog ────────────────────────────────────────────────────────────

function showReviewDialog(title) {
  const movie = moviesList.find(m => m.title.toLowerCase() === title.toLowerCase());
  const existing = movie ? (movie.review || '') : '';

  app.innerHTML = `
    <div class="screen editor-screen">
      <header class="app-header">
        <button id="back-btn" class="btn icon">&larr;</button>
        <h2>Review</h2>
        <button id="save-btn" class="btn primary">Save</button>
      </header>
      <h3>${esc(title)}</h3>
      <textarea id="review-text" class="review-textarea" placeholder="Write your review...">${esc(existing)}</textarea>
    </div>
  `;

  app.querySelector('#back-btn').addEventListener('click', () => showMovieList());
  app.querySelector('#save-btn').addEventListener('click', () => {
    const text = app.querySelector('#review-text').value.trim();
    if (!text) { alert('Please write a review'); return; }

    mutateLocal((lines) => {
      const found = findMovie(lines, title);
      if (!found) { alert(`"${title}" not found`); return lines; }
      setReview(lines, found.index, found.indent, text);
      return lines;
    }, `Add review: ${title}`);

    showMovieList();
  });
}

// ── Add/Edit Movie Screen ────────────────────────────────────────────────────

function showAddEdit(editTitle = null) {
  const isEdit = !!editTitle;
  let existing = null;
  if (isEdit && moviesList) {
    existing = moviesList.find(m => m.title.toLowerCase() === editTitle.toLowerCase());
  }

  app.innerHTML = `
    <div class="screen editor-screen">
      <header class="app-header">
        <button id="back-btn" class="btn icon">&larr;</button>
        <h2>${isEdit ? 'Edit Movie' : 'Add Movie'}</h2>
        <button id="save-btn" class="btn primary">${isEdit ? 'Update' : 'Add'}</button>
      </header>
      <div class="form-fields">
        <div class="form-group">
          <label for="field-title">Title *</label>
          <input type="text" id="field-title" placeholder="Movie title" value="${esc(existing ? existing.title : '')}">
        </div>
        <div class="form-group">
          <label for="field-director">Director</label>
          <input type="text" id="field-director" placeholder="Director name" value="${esc(existing ? (existing.director || '') : '')}">
        </div>
        <div class="form-group">
          <label for="field-year">Year</label>
          <input type="text" id="field-year" placeholder="Year" value="${esc(existing ? (existing.year || '') : '')}">
        </div>
        <div class="form-group">
          <label for="field-recommender">Recommended by</label>
          <input type="text" id="field-recommender" placeholder="Who recommended it?" value="${esc(existing ? (existing.recommender || '') : '')}">
        </div>
        <div class="form-group">
          <label for="field-review">Review</label>
          <textarea id="field-review" class="review-textarea" placeholder="Your review (optional)">${esc(existing ? (existing.review || '') : '')}</textarea>
        </div>
      </div>
    </div>
  `;

  app.querySelector('#back-btn').addEventListener('click', () => showMovieList());
  app.querySelector('#save-btn').addEventListener('click', () => {
    const title = app.querySelector('#field-title').value.trim();
    if (!title) { alert('Please enter a title'); return; }

    const director = app.querySelector('#field-director').value.trim();
    const year = app.querySelector('#field-year').value.trim();
    const recommender = app.querySelector('#field-recommender').value.trim();
    const review = app.querySelector('#field-review').value.trim();

    if (isEdit && existing) {
      mutateLocal((lines) => {
        const found = findMovie(lines, editTitle);
        if (!found) { alert(`"${editTitle}" not found`); return lines; }
        if (director) setProperty(lines, found.index, found.indent, 'Director', director);
        if (year) setProperty(lines, found.index, found.indent, 'Year', year);
        if (recommender) setProperty(lines, found.index, found.indent, 'Recommender', recommender);
        if (review) setReview(lines, found.index, found.indent, review);
        if (title !== editTitle) {
          lines[found.index] = lines[found.index].replace(editTitle, title);
        }
        return lines;
      }, `Update movie: ${title}`);
    } else {
      // Check duplicate
      if (findMovie(splitLines(moviesText), title)) {
        alert(`"${title}" already exists in your movie list.`);
        return;
      }

      mutateLocal((lines) => {
        const insert = findToWatchInsert(lines, recommender);
        if (!insert) { alert('Could not find insertion point'); return lines; }

        let insertIdx = insert.index;
        if (insert.newLines) {
          for (let i = 0; i < insert.newLines.length; i++) {
            lines.splice(insertIdx + i, 0, insert.newLines[i]);
          }
          insertIdx += insert.newLines.length;
        }

        const entry = buildMovieEntry(title, { recommender, director, year, review }, insert.indent);
        for (let i = 0; i < entry.length; i++) {
          lines.splice(insertIdx + i, 0, entry[i]);
        }
        return lines;
      }, `Add movie: ${title}`);
    }

    showMovieList();
  });
}

// ── Settings Screen ──────────────────────────────────────────────────────────

function showSettings() {
  app.innerHTML = `
    <div class="screen settings-screen">
      <header class="app-header">
        <button id="back-btn" class="btn icon">&larr;</button>
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
          <p class="muted">Movie Writer PWA. Changes are saved locally and synced to GitHub in the background. IMDb enrichment runs automatically via GitHub Actions after sync.</p>
        </div>
      </div>
    </div>
  `;

  app.querySelector('#back-btn').addEventListener('click', () => showMovieList());
  app.querySelector('#disconnect-btn').addEventListener('click', () => {
    if (confirm('Disconnect from GitHub?')) {
      clearToken();
      showSetup();
    }
  });
  app.querySelector('#force-sync-btn').addEventListener('click', async () => {
    const btn = app.querySelector('#force-sync-btn');
    btn.disabled = true;
    btn.textContent = 'Syncing...';
    await doSync();
    btn.disabled = false;
    btn.textContent = 'Force Sync Now';
    alert(await isDirty() ? 'Sync failed, will retry.' : 'Synced!');
  });
}

// ── Router ───────────────────────────────────────────────────────────────────

function route() {
  if (!isAuthenticated()) {
    showSetup();
  } else {
    showMovieList();
  }
}

route();
