// Main app controller and screen router

import { isAuthenticated, getToken, setToken, clearToken, validateToken } from './auth.js';
import { fetchPostList, loadPost, publishPost, updatePost, publishDraft } from './posts.js';
import { formatDate, parseFilename, displayDate, imageDir } from './naming.js';
import { buildPostContent, extractFromContent } from './frontmatter.js';
import { createEditor } from './editor.js';
import { renderPreview } from './preview.js';
import { pickImage, storeImage, getStoredImages, removeStoredImage, createThumbnailUrl, markdownImageRef } from './images.js';
import { suggestTags } from './tags.js';
import { saveDraft, getDraft, getAllDrafts, deleteDraft } from './storage.js';

const app = document.getElementById('app');
let currentScreen = null;
let currentDraftId = null;
let editor = null;
let attachedImages = [];
let editingPost = null; // { originalPath, ... } when editing existing post

// Screen navigation
function show(screenId) {
  currentScreen = screenId;
  window.location.hash = screenId;
}

// Setup screen
function showSetup() {
  app.innerHTML = `
    <div class="screen setup-screen">
      <h1>Blog Writer</h1>
      <p>Connect to your GitHub repo to start writing.</p>
      <ol>
        <li>Go to <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">GitHub Token Settings</a></li>
        <li>Set token name to "Blog Writer"</li>
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
  const error = app.querySelector('#setup-error');

  btn.addEventListener('click', async () => {
    const token = input.value.trim();
    if (!token) { error.textContent = 'Please enter a token'; error.hidden = false; return; }
    btn.disabled = true;
    btn.textContent = 'Validating...';
    const result = await validateToken(token);
    if (result.valid) {
      setToken(token);
      showPostList();
    } else {
      error.textContent = result.error;
      error.hidden = false;
      btn.disabled = false;
      btn.textContent = 'Connect';
    }
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') btn.click();
  });
}

// Post list screen
async function showPostList() {
  app.innerHTML = `
    <div class="screen list-screen">
      <header class="app-header">
        <h1>Blog Writer</h1>
        <div class="header-actions">
          <button id="refresh-btn" class="btn icon" title="Refresh">&#8635;</button>
          <button id="settings-btn" class="btn icon" title="Settings">&#9881;</button>
        </div>
      </header>
      <button id="new-post-btn" class="btn primary full-width">+ New Post</button>
      <div id="post-list" class="post-list">
        <div class="loading">Loading posts...</div>
      </div>
    </div>
  `;

  app.querySelector('#new-post-btn').addEventListener('click', () => showEditor());
  app.querySelector('#refresh-btn').addEventListener('click', () => loadPosts(true));
  app.querySelector('#settings-btn').addEventListener('click', showSettings);

  await loadPosts();
}

async function loadPosts(force = false) {
  const listEl = app.querySelector('#post-list');
  if (!listEl) return;

  try {
    const posts = await fetchPostList(force);
    if (!listEl.isConnected) return; // screen changed

    if (posts.length === 0) {
      listEl.innerHTML = '<p class="empty">No posts yet. Create your first one!</p>';
      return;
    }

    listEl.innerHTML = posts.map(p => `
      <div class="post-item" data-path="${p.path}">
        <div class="post-date">${p.date}</div>
        <div class="post-title">${escapeHtml(p.title)}${p.isDraft ? ' <span class="badge">draft</span>' : ''}</div>
      </div>
    `).join('');

    listEl.querySelectorAll('.post-item').forEach(el => {
      el.addEventListener('click', () => {
        const path = el.dataset.path;
        showEditor(path);
      });
    });
  } catch (err) {
    if (listEl.isConnected) {
      listEl.innerHTML = `<div class="error">Failed to load posts: ${escapeHtml(err.message)}</div>`;
    }
  }
}

// Editor screen
async function showEditor(existingPath = null) {
  editingPost = null;
  attachedImages = [];
  currentDraftId = existingPath || `new_${Date.now()}`;

  const today = new Date();
  let initialTitle = '';
  let initialTags = '';
  let initialBody = '';
  let initialDate = today.toISOString().slice(0, 10);

  app.innerHTML = `
    <div class="screen editor-screen">
      <header class="app-header">
        <button id="back-btn" class="btn icon">&larr;</button>
        <div class="header-actions">
          <button id="preview-btn" class="btn">Preview</button>
          <button id="draft-btn" class="btn">Save Draft</button>
          <button id="publish-btn" class="btn primary">Publish</button>
        </div>
      </header>
      <div class="editor-fields">
        <input type="text" id="field-title" placeholder="Post title" class="field-title">
        <div class="field-row">
          <input type="text" id="field-tags" placeholder="Tags (comma separated)">
          <button id="suggest-tags-btn" class="btn small">Suggest</button>
        </div>
        <div id="tag-suggestions" class="tag-suggestions" hidden></div>
        <input type="date" id="field-date" value="${initialDate}">
      </div>
      <div id="editor-container" class="editor-container"></div>
      <div id="preview-container" class="preview-container" hidden></div>
    </div>
  `;

  // If editing existing post, load it
  if (existingPath) {
    const titleEl = app.querySelector('#field-title');
    titleEl.value = 'Loading...';
    titleEl.disabled = true;

    try {
      const post = await loadPost(existingPath);
      editingPost = { originalPath: existingPath };
      initialTitle = post.title;
      initialTags = post.tags;
      initialBody = post.body;
      const parsed = parseFilename(existingPath.split('/').pop());
      if (parsed) {
        const ds = parsed.dateStr;
        initialDate = `${ds.slice(0,4)}-${ds.slice(4,6)}-${ds.slice(6,8)}`;
      }
    } catch (err) {
      app.querySelector('#field-title').value = '';
      app.querySelector('#field-title').disabled = false;
      alert('Failed to load post: ' + err.message);
    }
  }

  // Set field values
  const titleEl = app.querySelector('#field-title');
  const tagsEl = app.querySelector('#field-tags');
  const dateEl = app.querySelector('#field-date');
  titleEl.value = initialTitle;
  titleEl.disabled = false;
  tagsEl.value = initialTags;
  dateEl.value = initialDate;

  // Create editor
  const container = app.querySelector('#editor-container');
  editor = createEditor(container);
  editor.value = initialBody;

  // Image insertion
  editor.onImageRequest = async () => {
    const img = await pickImage();
    if (!img) return;
    const dateStr = dateEl.value.replace(/-/g, '');
    const record = await storeImage(currentDraftId, dateStr, img);
    attachedImages.push(record);
    const ref = markdownImageRef(dateStr, img.name);
    editor.insertAtCursor('\n' + ref + '\n');
    renderImageThumbs();
  };

  // Tag suggestions
  app.querySelector('#suggest-tags-btn').addEventListener('click', () => {
    const content = titleEl.value + '\n' + editor.value;
    const existing = tagsEl.value.split(',').map(t => t.trim()).filter(Boolean);
    const suggestions = suggestTags(content, existing);
    const sugEl = app.querySelector('#tag-suggestions');
    if (suggestions.length === 0) {
      sugEl.innerHTML = '<span class="muted">No suggestions</span>';
    } else {
      sugEl.innerHTML = suggestions.map(t =>
        `<button class="tag-chip" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</button>`
      ).join('');
      sugEl.querySelectorAll('.tag-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const current = tagsEl.value.split(',').map(s => s.trim()).filter(Boolean);
          if (!current.includes(chip.dataset.tag)) {
            current.push(chip.dataset.tag);
            tagsEl.value = current.join(', ');
          }
          chip.remove();
        });
      });
    }
    sugEl.hidden = false;
  });

  // Preview toggle
  let previewing = false;
  app.querySelector('#preview-btn').addEventListener('click', async () => {
    previewing = !previewing;
    const previewEl = app.querySelector('#preview-container');
    const editorEl = app.querySelector('#editor-container');
    const btn = app.querySelector('#preview-btn');

    if (previewing) {
      const fullContent = buildPostContent(titleEl.value, tagsEl.value, editor.value);
      // Build blob URL map for local images
      const blobMap = {};
      for (const img of attachedImages) {
        const ref = `files/${img.dateStr}/${img.name}`;
        blobMap[ref] = createThumbnailUrl(img);
      }
      const html = await renderPreview(fullContent, blobMap);
      previewEl.innerHTML = `<div class="preview-content">${html}</div>`;
      previewEl.hidden = false;
      editorEl.hidden = true;
      app.querySelector('.editor-fields').hidden = true;
      btn.textContent = 'Edit';
    } else {
      previewEl.hidden = true;
      editorEl.hidden = false;
      app.querySelector('.editor-fields').hidden = false;
      btn.textContent = 'Preview';
    }
  });

  // Back
  app.querySelector('#back-btn').addEventListener('click', () => {
    if (editor.value.trim() || titleEl.value.trim()) {
      if (!confirm('Discard unsaved changes?')) return;
    }
    showPostList();
  });

  // Save draft
  app.querySelector('#draft-btn').addEventListener('click', () => doPublish(true));

  // Publish
  app.querySelector('#publish-btn').addEventListener('click', () => doPublish(false));

  // Auto-save local draft every 30s
  const autoSaveInterval = setInterval(async () => {
    if (!app.querySelector('#field-title')) { clearInterval(autoSaveInterval); return; }
    await saveDraft({
      id: currentDraftId,
      title: titleEl.value,
      tags: tagsEl.value,
      body: editor.value,
      date: dateEl.value,
    });
  }, 30000);

  titleEl.focus();
}

async function doPublish(isDraft) {
  const titleEl = app.querySelector('#field-title');
  const tagsEl = app.querySelector('#field-tags');
  const dateEl = app.querySelector('#field-date');
  const title = titleEl.value.trim();
  const tags = tagsEl.value.trim();
  const body = editor.value;
  const date = new Date(dateEl.value + 'T00:00:00');

  if (!title) { alert('Please enter a title'); return; }

  // Show confirmation
  const dateStr = formatDate(date);
  const fileList = [`blog/${dateStr}_${title.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '')}.${isDraft ? 'draft' : 'md'}`];
  for (const img of attachedImages) {
    fileList.push(`blog/files/${dateStr}/${img.name}`);
  }

  const action = isDraft ? 'Save as draft' : 'Publish';
  const msg = `${action} "${title}"?\n\nFiles:\n${fileList.map(f => '  ' + f).join('\n')}`;
  if (!confirm(msg)) return;

  // Disable buttons
  const publishBtn = app.querySelector('#publish-btn');
  const draftBtn = app.querySelector('#draft-btn');
  publishBtn.disabled = true;
  draftBtn.disabled = true;
  publishBtn.textContent = isDraft ? 'Saving...' : 'Publishing...';

  try {
    if (editingPost) {
      await updatePost({
        originalPath: editingPost.originalPath,
        title, tags, body, date,
        newImages: attachedImages,
      });
    } else {
      await publishPost({
        title, tags, body, date,
        images: attachedImages,
        isDraft,
      });
    }

    // Clean up local draft
    await deleteDraft(currentDraftId);

    alert(isDraft
      ? 'Draft saved to GitHub!'
      : 'Published! Your post will be live in about 2 minutes after the build completes.');
    showPostList();
  } catch (err) {
    alert('Failed: ' + err.message);
    publishBtn.disabled = false;
    draftBtn.disabled = false;
    publishBtn.textContent = 'Publish';
  }
}

function renderImageThumbs() {
  const container = app.querySelector('#editor-images');
  if (!container) return;
  if (attachedImages.length === 0) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = attachedImages.map((img, i) => `
    <div class="image-thumb">
      <img src="${createThumbnailUrl(img)}" alt="${escapeHtml(img.name)}">
      <span class="image-name">${escapeHtml(img.name)}</span>
      <button class="btn-remove" data-index="${i}">&times;</button>
    </div>
  `).join('');
  container.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', async () => {
      const idx = parseInt(btn.dataset.index);
      const img = attachedImages[idx];
      await removeStoredImage(img.id);
      attachedImages.splice(idx, 1);
      renderImageThumbs();
    });
  });
}

// Settings screen
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
          <input type="password" id="current-token" value="${getToken() || ''}" readonly>
          <button id="disconnect-btn" class="btn danger">Disconnect</button>
        </div>
        <div class="form-group">
          <label>About</label>
          <p class="muted">Blog Writer PWA for k1monfared/notes. Posts are committed directly to the main branch.</p>
        </div>
      </div>
    </div>
  `;

  app.querySelector('#back-btn').addEventListener('click', showPostList);
  app.querySelector('#disconnect-btn').addEventListener('click', () => {
    if (confirm('Disconnect from GitHub? You will need to enter a new token.')) {
      clearToken();
      showSetup();
    }
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Router
function route() {
  if (!isAuthenticated()) {
    showSetup();
    return;
  }
  const hash = window.location.hash.slice(1);
  if (hash === 'settings') {
    showSettings();
  } else {
    showPostList();
  }
}

// Init
window.addEventListener('hashchange', route);
route();
