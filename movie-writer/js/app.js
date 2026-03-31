// Movie Writer PWA - Main app controller

import { isAuthenticated, getToken, setToken, clearToken, validateToken } from './auth.js';
import { getFile, createCommit } from './github.js';
import { setCache, getCache } from './storage.js';
import { parseMovies, findMovie, findInsertAfter, findToWatchInsert, buildMovieEntry, markWatched, setReview, setProperty } from './movies.js';

const app = document.getElementById('app');
let moviesText = null;  // raw text of movies.log
let moviesList = null;  // parsed movies

// ── Helpers ──────────────────────────────────────────────────────────────────

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function showLoading(msg = 'Loading...') {
  app.innerHTML = `<div class="screen"><div class="loading">${esc(msg)}</div></div>`;
}

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
          <button id="refresh-btn" class="btn icon" title="Refresh">&#8635;</button>
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
  app.querySelector('#refresh-btn').addEventListener('click', () => showMovieList(true));
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

    const query = (searchInput.value || '').toLowerCase().trim();
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

    // Expand/collapse
    listEl.querySelectorAll('.movie-header').forEach(header => {
      header.addEventListener('click', () => {
        const details = header.nextElementSibling;
        const icon = header.querySelector('.expand-icon');
        details.hidden = !details.hidden;
        icon.innerHTML = details.hidden ? '&#9660;' : '&#9650;';
      });
    });

    // Actions
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

  await loadMovies(forceRefresh);
  renderList();
}

async function loadMovies(force = false) {
  try {
    if (!force) {
      const cached = await getCache('moviesText');
      if (cached) {
        moviesText = cached;
        moviesList = parseMovies(moviesText);
        return;
      }
    }

    const file = await getFile('movies.log');
    moviesText = file.content;
    moviesList = parseMovies(moviesText);
    await setCache('moviesText', moviesText);
  } catch (err) {
    const listEl = app.querySelector('#movie-list');
    if (listEl) listEl.innerHTML = `<div class="error">Failed to load: ${esc(err.message)}</div>`;
  }
}

// ── Mark Watched ─────────────────────────────────────────────────────────────

async function doMarkWatched(title) {
  if (!confirm(`Mark "${title}" as watched?`)) return;

  // Prompt for optional review
  const review = prompt('Add a review? (optional, press Cancel to skip)');

  showLoading('Updating...');
  try {
    // Re-fetch to avoid conflicts
    const file = await getFile('movies.log');
    let lines = file.content.split('\n').map(l => l + '\n');
    // Fix last line
    if (lines.length > 0 && lines[lines.length - 1] === '\n') lines.pop();

    const found = findMovie(lines, title);
    if (!found) throw new Error(`Movie "${title}" not found`);

    markWatched(lines, found.index);
    if (review) {
      setReview(lines, found.index, found.indent, review);
    }

    const newContent = lines.join('').replace(/\n$/, '');
    await createCommit(
      [{ path: 'movies.log', content: newContent }],
      `Mark watched: ${title}`
    );

    moviesText = null; // invalidate cache
    await showMovieList(true);
  } catch (err) {
    alert('Failed: ' + err.message);
    showMovieList();
  }
}

async function doMarkUnwatched(title) {
  if (!confirm(`Mark "${title}" as unwatched?`)) return;

  showLoading('Updating...');
  try {
    const file = await getFile('movies.log');
    let lines = file.content.split('\n').map(l => l + '\n');
    if (lines.length > 0 && lines[lines.length - 1] === '\n') lines.pop();

    const found = findMovie(lines, title);
    if (!found) throw new Error(`Movie "${title}" not found`);

    // Replace [x] with []
    lines[found.index] = lines[found.index].replace(/\[[x\-? ]?\]/i, '[]');

    const newContent = lines.join('').replace(/\n$/, '');
    await createCommit(
      [{ path: 'movies.log', content: newContent }],
      `Mark unwatched: ${title}`
    );

    moviesText = null;
    await showMovieList(true);
  } catch (err) {
    alert('Failed: ' + err.message);
    showMovieList();
  }
}

// ── Review Dialog ────────────────────────────────────────────────────────────

function showReviewDialog(title) {
  // Find existing review
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
  app.querySelector('#save-btn').addEventListener('click', async () => {
    const text = app.querySelector('#review-text').value.trim();
    if (!text) { alert('Please write a review'); return; }

    const btn = app.querySelector('#save-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const file = await getFile('movies.log');
      let lines = file.content.split('\n').map(l => l + '\n');
      if (lines.length > 0 && lines[lines.length - 1] === '\n') lines.pop();

      const found = findMovie(lines, title);
      if (!found) throw new Error(`Movie "${title}" not found`);

      setReview(lines, found.index, found.indent, text);

      const newContent = lines.join('').replace(/\n$/, '');
      await createCommit(
        [{ path: 'movies.log', content: newContent }],
        `Add review: ${title}`
      );

      moviesText = null;
      showMovieList(true);
    } catch (err) {
      alert('Failed: ' + err.message);
      btn.disabled = false;
      btn.textContent = 'Save';
    }
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
  app.querySelector('#save-btn').addEventListener('click', async () => {
    const title = app.querySelector('#field-title').value.trim();
    if (!title) { alert('Please enter a title'); return; }

    const director = app.querySelector('#field-director').value.trim();
    const year = app.querySelector('#field-year').value.trim();
    const recommender = app.querySelector('#field-recommender').value.trim();
    const review = app.querySelector('#field-review').value.trim();

    const btn = app.querySelector('#save-btn');
    btn.disabled = true;
    btn.textContent = isEdit ? 'Updating...' : 'Adding...';

    try {
      // Re-fetch fresh copy
      const file = await getFile('movies.log');
      let lines = file.content.split('\n').map(l => l + '\n');
      if (lines.length > 0 && lines[lines.length - 1] === '\n') lines.pop();

      if (isEdit && existing) {
        // Update existing movie properties
        const found = findMovie(lines, editTitle);
        if (!found) throw new Error(`Movie "${editTitle}" not found`);

        if (director) setProperty(lines, found.index, found.indent, 'Director', director);
        if (year) setProperty(lines, found.index, found.indent, 'Year', year);
        if (recommender) setProperty(lines, found.index, found.indent, 'Recommender', recommender);
        if (review) setReview(lines, found.index, found.indent, review);

        // Update title if changed
        if (title !== editTitle) {
          lines[found.index] = lines[found.index].replace(editTitle, title);
        }

        const newContent = lines.join('').replace(/\n$/, '');
        await createCommit(
          [{ path: 'movies.log', content: newContent }],
          `Update movie: ${title}`
        );
      } else {
        // Check for duplicates
        if (findMovie(lines, title)) {
          alert(`"${title}" already exists in your movie list.`);
          btn.disabled = false;
          btn.textContent = 'Add';
          return;
        }

        // Find insert position
        const insert = findToWatchInsert(lines, recommender);
        if (!insert) throw new Error('Could not find insertion point in To Watch section');

        // If we need to create new subsection lines first
        let insertIdx = insert.index;
        if (insert.newLines) {
          for (let i = 0; i < insert.newLines.length; i++) {
            lines.splice(insertIdx + i, 0, insert.newLines[i]);
          }
          insertIdx += insert.newLines.length;
        }

        // Build and insert the movie entry
        const entry = buildMovieEntry(title, { recommender, director, year, review }, insert.indent);
        for (let i = 0; i < entry.length; i++) {
          lines.splice(insertIdx + i, 0, entry[i]);
        }

        const newContent = lines.join('').replace(/\n$/, '');
        await createCommit(
          [{ path: 'movies.log', content: newContent }],
          `Add movie: ${title}`
        );
      }

      moviesText = null;
      showMovieList(true);
    } catch (err) {
      alert('Failed: ' + err.message);
      btn.disabled = false;
      btn.textContent = isEdit ? 'Update' : 'Add';
    }
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
          <p class="muted">Movie Writer PWA for k1monfared/notes. Edits movies.log directly on the main branch. IMDb enrichment runs automatically via GitHub Actions after each push.</p>
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
