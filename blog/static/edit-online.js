(function () {
  'use strict';

  // ── 1. Constants & Config ─────────────────────────────────────────────────

  var TOKEN_KEY = 'gh_token';
  var REPO = 'k1monfared/notes';
  var API = 'https://api.github.com';
  var MAX_DIMENSION = 1600;
  var JPEG_QUALITY = 0.8;

  // ── 2. Auth ───────────────────────────────────────────────────────────────

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function setToken(t) { localStorage.setItem(TOKEN_KEY, t.trim()); }
  function clearToken() { localStorage.removeItem(TOKEN_KEY); }
  function isAuthenticated() { return !!getToken(); }

  function validateToken(token) {
    return fetch(API + '/repos/' + REPO, {
      headers: {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.github.v3+json',
      },
    })
    .then(function (res) {
      if (!res.ok) return { valid: false, error: 'HTTP ' + res.status };
      return res.json().then(function (data) {
        if (!data.permissions || !data.permissions.push) {
          return { valid: false, error: 'Token lacks write permission for this repo' };
        }
        return { valid: true };
      });
    })
    .catch(function (err) {
      return { valid: false, error: err.message };
    });
  }

  // ── 3. GitHub API ─────────────────────────────────────────────────────────

  function ghHeaders() {
    return {
      'Authorization': 'Bearer ' + getToken(),
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
    };
  }

  function ghRequest(path, options) {
    options = options || {};
    return fetch(API + path, Object.assign({ headers: ghHeaders() }, options))
      .then(function (res) {
        if (res.status === 401) {
          clearToken();
          document.body.classList.remove('edit-mode');
          showToast('Token expired. Please log in again.', 'error');
          throw new Error('Token expired');
        }
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (body) {
            throw new Error('GitHub API ' + res.status + ': ' + (body.message || res.statusText));
          });
        }
        if (res.status === 204) return null;
        return res.json();
      });
  }

  function listFiles(path) {
    return ghRequest('/repos/' + REPO + '/contents/' + path);
  }

  function getFile(path) {
    return ghRequest('/repos/' + REPO + '/contents/' + path).then(function (data) {
      var raw = atob(data.content.replace(/\n/g, ''));
      var bytes = Uint8Array.from(raw, function (c) { return c.charCodeAt(0); });
      var text = new TextDecoder().decode(bytes);
      return { content: text, sha: data.sha, path: data.path };
    });
  }

  function createCommit(files, message) {
    var refPath = '/repos/' + REPO + '/git/refs/heads/main';

    function attempt(n) {
      var baseSha, baseTreeSha;
      return ghRequest(refPath)
        .then(function (ref) {
          baseSha = ref.object.sha;
          return ghRequest('/repos/' + REPO + '/git/commits/' + baseSha);
        })
        .then(function (commit) {
          baseTreeSha = commit.tree.sha;
          var treeItems = [];
          var chain = Promise.resolve();
          files.forEach(function (file) {
            chain = chain.then(function () {
              return ghRequest('/repos/' + REPO + '/git/blobs', {
                method: 'POST',
                body: JSON.stringify({
                  content: file.content,
                  encoding: file.encoding === 'base64' ? 'base64' : 'utf-8',
                }),
              }).then(function (blob) {
                treeItems.push({ path: file.path, mode: '100644', type: 'blob', sha: blob.sha });
              });
            });
          });
          return chain.then(function () { return treeItems; });
        })
        .then(function (treeItems) {
          return ghRequest('/repos/' + REPO + '/git/trees', {
            method: 'POST',
            body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems }),
          });
        })
        .then(function (tree) {
          return ghRequest('/repos/' + REPO + '/git/commits', {
            method: 'POST',
            body: JSON.stringify({ message: message, tree: tree.sha, parents: [baseSha] }),
          });
        })
        .then(function (newCommit) {
          return ghRequest(refPath, {
            method: 'PATCH',
            body: JSON.stringify({ sha: newCommit.sha }),
          })
          .then(function () { return newCommit; })
          .catch(function (err) {
            if (err.message && err.message.indexOf('422') !== -1 && n < 2) {
              return attempt(n + 1);
            }
            throw err;
          });
        });
    }

    return attempt(0);
  }

  function renameFile(oldPath, newPath, content, message, extraFiles) {
    extraFiles = extraFiles || [];
    var refPath = '/repos/' + REPO + '/git/refs/heads/main';

    function attempt(n) {
      var baseSha, baseTreeSha;
      return ghRequest(refPath)
        .then(function (ref) {
          baseSha = ref.object.sha;
          return ghRequest('/repos/' + REPO + '/git/commits/' + baseSha);
        })
        .then(function (commit) {
          baseTreeSha = commit.tree.sha;
          return ghRequest('/repos/' + REPO + '/git/blobs', {
            method: 'POST',
            body: JSON.stringify({ content: content, encoding: 'utf-8' }),
          });
        })
        .then(function (blob) {
          var treeItems = [
            { path: newPath, mode: '100644', type: 'blob', sha: blob.sha },
            { path: oldPath, mode: '100644', type: 'blob', sha: null },
          ];
          var chain = Promise.resolve();
          extraFiles.forEach(function (file) {
            chain = chain.then(function () {
              return ghRequest('/repos/' + REPO + '/git/blobs', {
                method: 'POST',
                body: JSON.stringify({
                  content: file.content,
                  encoding: file.encoding === 'base64' ? 'base64' : 'utf-8',
                }),
              }).then(function (b) {
                treeItems.push({ path: file.path, mode: '100644', type: 'blob', sha: b.sha });
              });
            });
          });
          return chain.then(function () { return treeItems; });
        })
        .then(function (treeItems) {
          return ghRequest('/repos/' + REPO + '/git/trees', {
            method: 'POST',
            body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems }),
          });
        })
        .then(function (tree) {
          return ghRequest('/repos/' + REPO + '/git/commits', {
            method: 'POST',
            body: JSON.stringify({ message: message, tree: tree.sha, parents: [baseSha] }),
          });
        })
        .then(function (newCommit) {
          return ghRequest(refPath, {
            method: 'PATCH',
            body: JSON.stringify({ sha: newCommit.sha }),
          })
          .then(function () { return newCommit; })
          .catch(function (err) {
            if (err.message && err.message.indexOf('422') !== -1 && n < 2) {
              return attempt(n + 1);
            }
            throw err;
          });
        });
    }

    return attempt(0);
  }

  function deleteFile(path, message) {
    var refPath = '/repos/' + REPO + '/git/refs/heads/main';

    function attempt(n) {
      var baseSha;
      return ghRequest(refPath)
        .then(function (ref) {
          baseSha = ref.object.sha;
          return ghRequest('/repos/' + REPO + '/git/commits/' + baseSha);
        })
        .then(function (commit) {
          return ghRequest('/repos/' + REPO + '/git/trees', {
            method: 'POST',
            body: JSON.stringify({
              base_tree: commit.tree.sha,
              tree: [{ path: path, mode: '100644', type: 'blob', sha: null }],
            }),
          });
        })
        .then(function (tree) {
          return ghRequest('/repos/' + REPO + '/git/commits', {
            method: 'POST',
            body: JSON.stringify({ message: message, tree: tree.sha, parents: [baseSha] }),
          });
        })
        .then(function (newCommit) {
          return ghRequest(refPath, {
            method: 'PATCH',
            body: JSON.stringify({ sha: newCommit.sha }),
          })
          .then(function () { return newCommit; })
          .catch(function (err) {
            if (err.message && err.message.indexOf('422') !== -1 && n < 2) {
              return attempt(n + 1);
            }
            throw err;
          });
        });
    }

    return attempt(0);
  }

  // ── 4. Frontmatter & Naming ───────────────────────────────────────────────

  function parseFrontmatter(text) {
    var meta = {};
    if (!text.startsWith('---')) return { meta: meta, body: text };
    var parts = text.split('---', 3);
    if (parts.length < 3) return { meta: meta, body: text };
    parts[1].trim().split('\n').forEach(function (line) {
      var idx = line.indexOf(':');
      if (idx === -1) return;
      var key = line.slice(0, idx).trim().toLowerCase();
      var val = line.slice(idx + 1).trim();
      meta[key] = val;
    });
    return { meta: meta, body: parts[2] };
  }

  function generateFrontmatter(meta) {
    var lines = [];
    Object.keys(meta).forEach(function (key) {
      if (meta[key]) lines.push(key + ': ' + meta[key]);
    });
    if (lines.length === 0) return '';
    return '---\n' + lines.join('\n') + '\n---\n';
  }

  function buildPostContent(title, tags, body) {
    var meta = {};
    if (tags.trim()) meta.tags = tags.trim();
    var frontmatter = generateFrontmatter(meta);
    var heading = '# ' + title.trim() + '\n\n';
    return frontmatter + heading + body.trim() + '\n';
  }

  function extractFromContent(content) {
    var parsed = parseFrontmatter(content);
    var tags = parsed.meta.tags || '';
    var title = '';
    var bodyWithoutTitle = parsed.body;
    var lines = parsed.body.trim().split('\n');

    for (var i = 0; i < lines.length; i++) {
      var match = lines[i].trim().match(/^#{1,6}\s+(.+?)(?:\s*#*\s*)?$/);
      if (match) {
        title = match[1].replace(/\*\*(.+?)\*\*/g, '$1').trim();
        bodyWithoutTitle = lines.slice(0, i).concat(lines.slice(i + 1)).join('\n').trim();
        break;
      }
      if (i + 1 < lines.length && lines[i].trim() && /^[=-]+$/.test(lines[i + 1].trim())) {
        title = lines[i].trim().replace(/\*\*(.+?)\*\*/g, '$1');
        bodyWithoutTitle = lines.slice(0, i).concat(lines.slice(i + 2)).join('\n').trim();
        break;
      }
    }

    return { title: title, tags: tags, body: bodyWithoutTitle };
  }

  function fmtDate(date) {
    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, '0');
    var d = String(date.getDate()).padStart(2, '0');
    return '' + y + m + d;
  }

  function displayDate(dateStr) {
    var y = parseInt(dateStr.slice(0, 4));
    var m = parseInt(dateStr.slice(4, 6)) - 1;
    var d = parseInt(dateStr.slice(6, 8));
    return new Date(y, m, d).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  }

  function titleToSlug(title) {
    return title
      .toLowerCase()
      .trim()
      .replace(/[^\w\s\u0600-\u06FF\u0750-\u077F]/g, '')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  function generateFilename(date, title, isDraft) {
    var dateStr = fmtDate(date);
    var slug = titleToSlug(title);
    var ext = isDraft ? 'draft' : 'md';
    return dateStr + '_' + slug + '.' + ext;
  }

  function parseFilename(filename) {
    var stem = filename.replace(/\.(md|draft)$/, '');
    var match = stem.match(/^(\d{8})_(.+)$/);
    if (!match) return null;
    return {
      dateStr: match[1],
      slug: match[2],
      urlSlug: match[1] + '-' + match[2].replace(/_/g, '-'),
      isDraft: filename.endsWith('.draft'),
    };
  }

  function imageDir(dateStr) {
    return 'files/' + dateStr;
  }

  // ── 5. Image Handling ─────────────────────────────────────────────────────

  function sanitizeImageName(name) {
    return name.toLowerCase().replace(/\s+/g, '_').replace(/[^\w.\-]/g, '');
  }

  function arrayBufferToBase64(buffer) {
    var bytes = new Uint8Array(buffer);
    var binary = '';
    for (var i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  function pickImage() {
    return new Promise(function (resolve) {
      var input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/png,image/jpeg,image/gif';
      input.capture = 'environment';
      input.onchange = function () {
        if (!input.files || !input.files[0]) { resolve(null); return; }
        processImage(input.files[0]).then(resolve);
      };
      input.click();
    });
  }

  function processImage(file) {
    if (file.type === 'image/gif') {
      return file.arrayBuffer().then(function (buffer) {
        return {
          name: sanitizeImageName(file.name),
          type: 'image/gif',
          base64: arrayBufferToBase64(buffer),
          blob: new Blob([buffer], { type: 'image/gif' }),
        };
      });
    }

    return createImageBitmap(file).then(function (bitmap) {
      var w = bitmap.width, h = bitmap.height;
      if (w > MAX_DIMENSION || h > MAX_DIMENSION) {
        if (w > h) { h = Math.round(h * MAX_DIMENSION / w); w = MAX_DIMENSION; }
        else { w = Math.round(w * MAX_DIMENSION / h); h = MAX_DIMENSION; }
      }
      var canvas = new OffscreenCanvas(w, h);
      var ctx = canvas.getContext('2d');
      ctx.drawImage(bitmap, 0, 0, w, h);
      bitmap.close();

      var isPng = file.type === 'image/png';
      var outputType = isPng ? 'image/png' : 'image/jpeg';
      var quality = isPng ? undefined : JPEG_QUALITY;
      return canvas.convertToBlob({ type: outputType, quality: quality }).then(function (blob) {
        return blob.arrayBuffer();
      }).then(function (buffer) {
        var name = sanitizeImageName(file.name);
        if (!isPng && !name.endsWith('.jpg') && !name.endsWith('.jpeg')) {
          name = name.replace(/\.[^.]+$/, '.jpg');
        }
        return { name: name, type: outputType, base64: arrayBufferToBase64(buffer), blob: new Blob([buffer], { type: outputType }) };
      });
    });
  }

  function markdownImageRef(dateStr, imageName) {
    return '![](files/' + dateStr + '/' + imageName + ')';
  }

  // ── 6. Tag Suggestions ────────────────────────────────────────────────────

  var TAG_KEYWORDS = {
    'linear algebra': [1, ['linear algebra', 'matrices', 'vector space', 'row reduction']],
    'eigenvalue': [1, ['eigenvalue', 'eigenvector', 'eigenspace']],
    'statistics': [1, ['statistics', 'statistical', 'hypothesis test', 'p-value', 'confidence interval']],
    'probability': [1, ['probability', 'probabilistic', 'expected value', 'random variable']],
    'combinatorics': [1, ['combinatorics', 'combinatorial', 'binomial coefficient']],
    'geometry': [1, ['geometry', 'geometric', 'polygon', 'fractal', 'tesselation']],
    'number theory': [1, ['number theory', 'prime number', 'modular arithmetic']],
    'dynamical systems': [1, ['dynamical system', 'differential equation', 'attractor']],
    'calculus': [1, ['calculus', 'derivative', 'integral', 'taylor series']],
    'graph': [1, ['graph theory', 'adjacency matrix', 'vertex', 'vertices']],
    'math': [2, ['mathematic', 'theorem', 'proof', 'lemma', 'conjecture', 'equation']],
    'music': [1, ['music', 'album', 'musician', 'composer', 'melody', 'symphony']],
    'concert': [1, ['concert', 'live performance', 'recital']],
    'piano': [1, ['piano', 'pianist']],
    'cello': [1, ['cello', 'cellist']],
    'classical': [1, ['classical music', 'baroque', 'vivaldi', 'beethoven', 'mozart']],
    'linux': [1, ['linux', 'ubuntu', 'gnome', 'sudo apt']],
    'bash': [1, ['#!/bin/bash', 'bash script', 'bash command']],
    'python': [1, ['python3', 'import numpy', 'import pandas', '.py ', 'pip install']],
    'sage': [1, ['sagemath', 'sage(']],
    'teaching': [2, ['teaching', 'classroom', 'students', 'instructor', 'syllabus', 'lecture', 'course']],
    'education': [1, ['education', 'curriculum', 'pedagogy']],
    'life': [2, ['my life', "i've been", 'personal', 'recently']],
    'philosophy': [1, ['philosophy', 'philosophical', 'epistemolog']],
    'observation': [1, ['observation', 'i noticed', 'interesting pattern']],
    'depression': [1, ['depression', 'depressed', 'mental health']],
    'movie': [1, ['movie', 'film', 'cinema', 'director']],
    'book': [1, ['book review', 'i read a book', 'this book']],
    'poetry': [1, ['poem', 'poetry', 'stanza']],
    'politics': [1, ['politics', 'political', 'government', 'democracy']],
    'immigration': [1, ['immigration', 'immigrant', 'visa', 'citizenship', 'refugee']],
    'racism': [1, ['racism', 'racist', 'racial discrimination']],
    'publication': [2, ['published', 'journal', 'accepted', 'peer review']],
    'paper': [1, ['our paper', 'this paper', 'the paper', 'manuscript']],
    'talk': [1, ['gave a talk', 'seminar talk', 'my talk', 'invited talk']],
    'conference': [1, ['conference', 'workshop', 'symposium']],
    'academia': [2, ['academia', 'academic', 'university', 'professor', 'faculty', 'department']],
    'finance': [1, ['finance', 'financial', 'tax', 'budget', 'investment']],
    'health': [1, ['bpa', 'bisphenol', 'endocrine disruptor']],
    'privacy': [1, ['privacy', 'end-to-end encryption', 'e2ee', 'surveillance']],
  };

  var BROAD_TAGS = ['math', 'music', 'linux', 'teaching', 'life', 'politics', 'publication', 'finance'];

  function suggestTags(content, existingTags) {
    existingTags = existingTags || [];
    var lower = content.toLowerCase();
    var existingSet = {};
    existingTags.forEach(function (t) { existingSet[t.trim().toLowerCase()] = true; });

    var scores = {};
    Object.keys(TAG_KEYWORDS).forEach(function (tag) {
      if (existingSet[tag]) return;
      var entry = TAG_KEYWORDS[tag];
      var minHits = entry[0], keywords = entry[1];
      var hits = keywords.filter(function (kw) { return lower.indexOf(kw.toLowerCase()) !== -1; }).length;
      if (hits >= minHits) scores[tag] = hits;
    });

    var suggested = Object.keys(scores).sort(function (a, b) { return scores[b] - scores[a]; });
    if (suggested.length > 6) suggested = suggested.slice(0, 6);

    var all = Object.keys(existingSet).concat(suggested);
    var hasBroad = all.some(function (t) { return BROAD_TAGS.indexOf(t) !== -1; });
    if (!hasBroad) suggested.push('life');

    return suggested;
  }

  // ── 7. Commit Queue ───────────────────────────────────────────────────────

  var commitQueue = [];
  var commitInFlight = false;

  function enqueueCommit(commitFn, successMsg) {
    commitQueue.push({ fn: commitFn, msg: successMsg || 'Saved' });
    processQueue();
  }

  function processQueue() {
    if (commitInFlight || commitQueue.length === 0) return;
    commitInFlight = true;
    var item = commitQueue.shift();
    item.fn()
      .then(function () {
        showToast(item.msg, 'success');
        commitInFlight = false;
        processQueue();
      })
      .catch(function (err) {
        showToast('Save failed: ' + err.message, 'error');
        commitInFlight = false;
        processQueue();
      });
  }

  // ── 8. Toast Notifications ────────────────────────────────────────────────

  var toastEl = null;
  var toastTimer = null;

  function showToast(msg, type) {
    type = type || 'info';
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'edit-toast';
      document.body.appendChild(toastEl);
    }
    clearTimeout(toastTimer);
    toastEl.textContent = msg;
    toastEl.className = 'edit-toast toast-' + type;
    requestAnimationFrame(function () {
      toastEl.classList.add('visible');
    });
    if (type !== 'error') {
      toastTimer = setTimeout(function () {
        toastEl.classList.remove('visible');
      }, 3000);
    }
    toastEl.onclick = function () {
      toastEl.classList.remove('visible');
    };
  }

  // ── 9. Page Detection & URL Mapping ───────────────────────────────────────

  var article = document.querySelector('article');
  var isPostPage = !!article;
  var postList = document.querySelector('.post-list');
  var h1El = document.querySelector('main h1');
  var h1Text = h1El ? h1El.textContent : '';
  var isTagPage = !isPostPage && h1Text.indexOf('Posts tagged:') === 0;
  var isIndexPage = !isPostPage && !isTagPage && !!postList;

  function getUrlSlug() {
    var path = window.location.pathname;
    // Path like /notes/blog/20260329-bale-trap/ or /notes/blog/20260329-bale-trap/index.html
    var parts = path.replace(/\/index\.html$/, '').replace(/\/$/, '').split('/');
    return parts[parts.length - 1];
  }

  function urlSlugToFileStem(urlSlug) {
    var m = urlSlug.match(/^(\d{8})-(.+)$/);
    return m ? m[1] + '_' + m[2].replace(/-/g, '_') : null;
  }

  function fileStemToUrlSlug(stem) {
    var m = stem.match(/^(\d{8})_(.+)$/);
    return m ? m[1] + '-' + m[2].replace(/_/g, '-') : null;
  }

  // ── 10. Auth UI ───────────────────────────────────────────────────────────

  function showLoginDialog() {
    var overlay = document.createElement('div');
    overlay.className = 'edit-auth-overlay';
    overlay.innerHTML =
      '<div class="edit-auth-dialog">' +
        '<h3>Connect to GitHub</h3>' +
        '<p>Enter a fine-grained Personal Access Token for <code>' + REPO + '</code> with Contents read/write permission. ' +
        '<a href="https://github.com/settings/tokens?type=beta" target="_blank" rel="noopener">Create one here</a>.</p>' +
        '<input type="password" id="edit-token-input" placeholder="github_pat_..." autocomplete="off">' +
        '<div class="edit-auth-error" id="edit-auth-error"></div>' +
        '<div class="edit-auth-buttons">' +
          '<button type="button" id="edit-auth-cancel">Cancel</button>' +
          '<button type="button" id="edit-auth-connect" class="btn-primary">Connect</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);

    var input = overlay.querySelector('#edit-token-input');
    var errorEl = overlay.querySelector('#edit-auth-error');
    var connectBtn = overlay.querySelector('#edit-auth-connect');
    var cancelBtn = overlay.querySelector('#edit-auth-cancel');

    input.focus();

    connectBtn.addEventListener('click', function () {
      var token = input.value.trim();
      if (!token) { errorEl.textContent = 'Please enter a token.'; errorEl.style.display = 'block'; return; }
      connectBtn.disabled = true;
      connectBtn.textContent = 'Validating...';
      validateToken(token).then(function (result) {
        if (result.valid) {
          setToken(token);
          overlay.remove();
          activateEditMode();
        } else {
          errorEl.textContent = result.error;
          errorEl.style.display = 'block';
          connectBtn.disabled = false;
          connectBtn.textContent = 'Connect';
        }
      });
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') connectBtn.click();
    });

    cancelBtn.addEventListener('click', function () {
      overlay.remove();
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) overlay.remove();
    });

    document.addEventListener('keydown', function onEsc(e) {
      if (e.key === 'Escape' && document.body.contains(overlay)) {
        overlay.remove();
        document.removeEventListener('keydown', onEsc);
      }
    });
  }

  function setupLockButton() {
    var btn = document.getElementById('edit-lock');
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (isAuthenticated()) {
        if (confirm('Disconnect from edit mode?')) {
          clearToken();
          location.reload();
        }
      } else {
        showLoginDialog();
      }
    });
  }

  // ── 11. Draft Fetching & Index Page Injection ─────────────────────────────

  function loadDraftsOnIndex() {
    if (!isIndexPage || !postList) return;

    var loading = document.createElement('div');
    loading.className = 'edit-loading edit-only';
    loading.textContent = 'Loading drafts...';
    postList.parentNode.insertBefore(loading, postList);

    listFiles('blog')
      .then(function (files) {
        var drafts = files.filter(function (f) {
          return f.type === 'file' && f.name.endsWith('.draft') && /^\d{8}_/.test(f.name);
        });
        if (drafts.length === 0) { loading.remove(); return; }

        var chain = Promise.resolve();
        var draftData = [];
        drafts.forEach(function (draft) {
          chain = chain.then(function () {
            return getFile(draft.path).then(function (file) {
              var parsed = parseFilename(draft.name);
              var extracted = extractFromContent(file.content);
              draftData.push({
                path: draft.path,
                filename: draft.name,
                dateStr: parsed ? parsed.dateStr : '',
                title: extracted.title || (parsed ? parsed.slug.replace(/_/g, ' ') : draft.name),
                tags: extracted.tags,
                date: parsed ? displayDate(parsed.dateStr) : '',
              });
            }).catch(function () { /* skip unreadable drafts */ });
          });
        });

        return chain.then(function () {
          loading.remove();
          draftData.sort(function (a, b) { return b.dateStr.localeCompare(a.dateStr); });
          draftData.forEach(function (d) { insertDraftItem(d); });
        });
      })
      .catch(function (err) {
        loading.remove();
        showToast('Failed to load drafts: ' + err.message, 'error');
      });
  }

  function insertDraftItem(draft) {
    var li = document.createElement('li');
    li.className = 'draft-item';
    li.setAttribute('data-path', draft.path);

    var tagChips = '';
    if (draft.tags) {
      tagChips = draft.tags.split(',').map(function (t) {
        t = t.trim();
        return '<a href="tag/' + encodeURIComponent(t) + '/" class="tag">' + escapeHtml(t) + '</a>';
      }).join(' ');
    }

    li.innerHTML =
      '<a href="javascript:void(0)">' +
        '<span class="post-title">' + escapeHtml(draft.title) + ' <span class="draft-badge">draft</span></span>' +
        '<span class="post-date">' + escapeHtml(draft.date) + '</span>' +
      '</a>' +
      '<div class="post-meta-line"><span class="tag-chips">' + tagChips + '</span></div>';

    li.querySelector('a').addEventListener('click', function (e) {
      e.preventDefault();
      openEditor({ path: draft.path, isDraft: true });
    });

    // Insert at the top (drafts are usually recent)
    if (postList.firstChild) {
      postList.insertBefore(li, postList.firstChild);
    } else {
      postList.appendChild(li);
    }
  }

  // ── 12. Editor Overlay ────────────────────────────────────────────────────

  var savedMainContent = null;
  var pendingImages = [];

  function openEditor(opts) {
    opts = opts || {};
    var mainEl = document.querySelector('main.container');
    if (!mainEl) return;

    savedMainContent = mainEl.innerHTML;
    pendingImages = [];

    var isNew = !opts.path;
    var isDraft = !!opts.isDraft;
    var originalPath = opts.path || '';

    var today = new Date();
    var dateVal = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

    mainEl.innerHTML =
      '<div class="editor-overlay">' +
        '<div class="editor-field">' +
          '<label for="edit-title">Title</label>' +
          '<input type="text" id="edit-title" placeholder="Post title...">' +
        '</div>' +
        '<div class="editor-tags-row">' +
          '<div class="editor-field">' +
            '<label for="edit-tags">Tags</label>' +
            '<input type="text" id="edit-tags" placeholder="tag1, tag2, tag3">' +
          '</div>' +
          '<button type="button" class="suggest-btn" id="edit-suggest-tags">Suggest</button>' +
        '</div>' +
        '<div class="tag-suggestions" id="edit-tag-suggestions"></div>' +
        '<div class="editor-field">' +
          '<label for="edit-date">Date</label>' +
          '<input type="date" id="edit-date" value="' + dateVal + '">' +
        '</div>' +
        '<div class="editor-toolbar">' +
          '<button type="button" data-action="bold" title="Bold">B</button>' +
          '<button type="button" data-action="italic" title="Italic">I</button>' +
          '<button type="button" data-action="heading" title="Heading">H</button>' +
          '<button type="button" data-action="link" title="Link">&#128279;</button>' +
          '<button type="button" data-action="image" title="Insert Image">&#128247;</button>' +
          '<button type="button" data-action="hr" title="Horizontal Rule">&mdash;</button>' +
        '</div>' +
        '<textarea id="edit-body" placeholder="Write your post here..."></textarea>' +
        '<div class="editor-images" id="edit-images"></div>' +
        '<div id="edit-preview" class="editor-preview" style="display:none"></div>' +
        '<div class="editor-actions" id="edit-actions"></div>' +
      '</div>';

    var titleInput = mainEl.querySelector('#edit-title');
    var tagsInput = mainEl.querySelector('#edit-tags');
    var dateInput = mainEl.querySelector('#edit-date');
    var bodyTextarea = mainEl.querySelector('#edit-body');
    var previewEl = mainEl.querySelector('#edit-preview');
    var actionsEl = mainEl.querySelector('#edit-actions');
    var imagesEl = mainEl.querySelector('#edit-images');
    var suggestionsEl = mainEl.querySelector('#edit-tag-suggestions');
    var showingPreview = false;

    // Toolbar
    mainEl.querySelector('.editor-toolbar').addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var action = btn.dataset.action;
      if (action === 'image') {
        handleImageInsert(bodyTextarea, dateInput, imagesEl);
        return;
      }
      applyToolbarAction(bodyTextarea, action);
    });

    // Tag suggestions
    mainEl.querySelector('#edit-suggest-tags').addEventListener('click', function () {
      var existing = tagsInput.value.split(',').map(function (t) { return t.trim(); }).filter(Boolean);
      var content = titleInput.value + ' ' + bodyTextarea.value;
      var suggestions = suggestTags(content, existing);
      suggestionsEl.innerHTML = '';
      suggestions.forEach(function (tag) {
        var chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.textContent = tag;
        chip.addEventListener('click', function () {
          var current = tagsInput.value.trim();
          tagsInput.value = current ? current + ', ' + tag : tag;
          chip.remove();
        });
        suggestionsEl.appendChild(chip);
      });
    });

    // Build action buttons
    function addBtn(label, cls, handler) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = label;
      if (cls) btn.className = cls;
      btn.addEventListener('click', handler);
      actionsEl.appendChild(btn);
      return btn;
    }

    if (isNew || isDraft) {
      addBtn('Save Draft', 'btn-save', function () {
        doSave(true);
      });
      addBtn('Publish', 'btn-publish', function () {
        doSave(false);
      });
    } else {
      addBtn('Save', 'btn-save', function () {
        doSave(false);
      });
      addBtn('Unpublish', 'btn-unpublish', function () {
        doUnpublish();
      });
    }

    addBtn('Preview', '', function () {
      showingPreview = !showingPreview;
      if (showingPreview) {
        previewEl.innerHTML = typeof marked !== 'undefined' ? marked.parse(bodyTextarea.value, { breaks: true, gfm: true }) : bodyTextarea.value;
        bodyTextarea.style.display = 'none';
        mainEl.querySelector('.editor-toolbar').style.display = 'none';
        previewEl.style.display = 'block';
        this.textContent = 'Edit';
      } else {
        bodyTextarea.style.display = '';
        mainEl.querySelector('.editor-toolbar').style.display = '';
        previewEl.style.display = 'none';
        this.textContent = 'Preview';
      }
    });

    // Delete button for existing posts/drafts
    if (!isNew) {
      addBtn('Delete', 'btn-danger', function () {
        if (!confirm('Are you sure you want to delete this post? This cannot be undone.')) return;
        var title = titleInput.value.trim() || 'Untitled';
        enqueueCommit(function () {
          return deleteFile(originalPath, 'Delete: ' + title);
        }, 'Deleted. Site rebuilds in ~2 minutes.');
        closeEditor();
      });
    }

    addBtn('Cancel', 'btn-cancel', function () {
      closeEditor();
    });

    // Escape key to cancel editing
    function onEditorEsc(e) {
      if (e.key === 'Escape') {
        closeEditor();
        document.removeEventListener('keydown', onEditorEsc);
      }
    }
    document.addEventListener('keydown', onEditorEsc);

    // Detect RTL from the article element if on a post page
    if (isPostPage && article && article.getAttribute('dir') === 'rtl') {
      bodyTextarea.setAttribute('dir', 'rtl');
      titleInput.setAttribute('dir', 'rtl');
    }

    // Load existing content
    if (!isNew && originalPath) {
      titleInput.disabled = true;
      bodyTextarea.disabled = true;
      bodyTextarea.placeholder = 'Loading...';
      getFile(originalPath)
        .then(function (file) {
          var extracted = extractFromContent(file.content);
          titleInput.value = extracted.title;
          tagsInput.value = extracted.tags;
          bodyTextarea.value = extracted.body;
          // Parse date from filename
          var fn = originalPath.split('/').pop();
          var parsed = parseFilename(fn);
          if (parsed) {
            var ds = parsed.dateStr;
            dateInput.value = ds.slice(0, 4) + '-' + ds.slice(4, 6) + '-' + ds.slice(6, 8);
          }
          // Auto-detect RTL from content (Persian/Arabic range)
          if (/[\u0600-\u06FF\u0750-\u077F]/.test(extracted.title + extracted.body)) {
            bodyTextarea.setAttribute('dir', 'rtl');
            titleInput.setAttribute('dir', 'rtl');
          }
          titleInput.disabled = false;
          bodyTextarea.disabled = false;
          bodyTextarea.placeholder = 'Write your post here...';
          titleInput.focus();
        })
        .catch(function (err) {
          showToast('Failed to load post: ' + err.message, 'error');
          closeEditor();
        });
    } else {
      titleInput.focus();
    }

    window.scrollTo(0, 0);

    // Save handlers
    function doSave(asDraft) {
      var title = titleInput.value.trim();
      if (!title) { showToast('Title is required', 'error'); return; }
      var tags = tagsInput.value.trim();
      var body = bodyTextarea.value;
      var dateParts = dateInput.value.split('-');
      var date = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]));
      var dateStr = fmtDate(date);

      var content = buildPostContent(title, tags, body);
      var filename = generateFilename(date, title, asDraft);
      var newPath = 'blog/' + filename;

      var imageFiles = pendingImages.map(function (img) {
        return {
          path: 'blog/' + imageDir(dateStr) + '/' + img.name,
          content: img.base64,
          encoding: 'base64',
        };
      });

      var action = asDraft ? 'Save draft' : (isNew ? 'Add blog post' : 'Update blog post');
      var message = action + ': ' + title;

      if (isNew) {
        enqueueCommit(function () {
          var files = [{ path: newPath, content: content, encoding: 'utf-8' }].concat(imageFiles);
          return createCommit(files, message);
        }, asDraft ? 'Draft saved' : 'Published! Site rebuilds in ~2 minutes.');
      } else if (originalPath !== newPath) {
        // Path changed: rename
        enqueueCommit(function () {
          return renameFile(originalPath, newPath, content, message, imageFiles);
        }, asDraft ? 'Draft saved' : 'Published! Site rebuilds in ~2 minutes.');
      } else {
        enqueueCommit(function () {
          var files = [{ path: newPath, content: content, encoding: 'utf-8' }].concat(imageFiles);
          return createCommit(files, message);
        }, 'Saved! Site rebuilds in ~2 minutes.');
      }

      // Close editor first (restores original DOM), then apply optimistic update
      var shouldUpdateDOM = isPostPage && !asDraft;
      closeEditor();

      if (shouldUpdateDOM) {
        updatePostDOM(title, tags, body);
      }
    }

    function doUnpublish() {
      var title = titleInput.value.trim();
      if (!title) { showToast('Title is required', 'error'); return; }
      var tags = tagsInput.value.trim();
      var body = bodyTextarea.value;
      var dateParts = dateInput.value.split('-');
      var date = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]));
      var content = buildPostContent(title, tags, body);
      var filename = generateFilename(date, title, true);
      var newPath = 'blog/' + filename;
      var message = 'Unpublish: ' + title;

      enqueueCommit(function () {
        return renameFile(originalPath, newPath, content, message);
      }, 'Unpublished. Post moved to drafts.');

      closeEditor();
    }
  }

  function closeEditor() {
    var mainEl = document.querySelector('main.container');
    if (mainEl && savedMainContent !== null) {
      mainEl.innerHTML = savedMainContent;
      savedMainContent = null;
      pendingImages = [];
      // Re-attach edit controls if still in edit mode
      if (isAuthenticated()) {
        if (isPostPage) addPostPageControls();
        if (isIndexPage) addIndexPageControls();
      }
    }
  }

  function updatePostDOM(title, tags, body) {
    var h1 = document.querySelector('article h1');
    if (h1) h1.textContent = title;

    var metaEl = document.querySelector('article .post-meta');
    if (metaEl && tags) {
      var dateSpan = metaEl.childNodes[0];
      var dateText = dateSpan ? dateSpan.textContent : '';
      var chips = tags.split(',').map(function (t) {
        t = t.trim();
        return '<a href="tag/' + encodeURIComponent(t) + '/" class="tag">' + escapeHtml(t) + '</a>';
      }).join(' ');
      metaEl.innerHTML = escapeHtml(dateText) + ' <span class="tag-chips">' + chips + '</span>';
    }

    // Re-render body
    var bodyContainer = article;
    if (bodyContainer && typeof marked !== 'undefined') {
      // Find content between h1/meta and post-nav
      var nav = bodyContainer.querySelector('.post-nav');
      var comments = bodyContainer.querySelector('.comments');
      var h1El = bodyContainer.querySelector('h1');
      var metaEl2 = bodyContainer.querySelector('.post-meta');

      // Remove everything between meta and nav
      var toRemove = [];
      var el = metaEl2 ? metaEl2.nextSibling : (h1El ? h1El.nextSibling : null);
      while (el && el !== nav && el !== comments) {
        toRemove.push(el);
        el = el.nextSibling;
      }
      toRemove.forEach(function (n) { n.remove(); });

      // Insert new rendered content
      var rendered = document.createElement('div');
      rendered.innerHTML = marked.parse(body, { breaks: true, gfm: true });
      var insertBefore = nav || comments;
      if (insertBefore) {
        while (rendered.firstChild) {
          bodyContainer.insertBefore(rendered.firstChild, insertBefore);
        }
      }
    }
  }

  function handleImageInsert(textarea, dateInput, imagesEl) {
    pickImage().then(function (img) {
      if (!img) return;
      pendingImages.push(img);

      var dateParts = dateInput.value.split('-');
      var dateStr = dateParts[0] + dateParts[1] + dateParts[2];
      var ref = markdownImageRef(dateStr, img.name);

      // Insert at cursor
      var start = textarea.selectionStart;
      var before = textarea.value.slice(0, start);
      var after = textarea.value.slice(textarea.selectionEnd);
      textarea.value = before + '\n' + ref + '\n' + after;
      textarea.selectionStart = textarea.selectionEnd = start + ref.length + 2;
      textarea.focus();

      // Add thumbnail
      var thumb = document.createElement('div');
      thumb.className = 'img-thumb';
      var thumbImg = document.createElement('img');
      if (img.blob) {
        thumbImg.src = URL.createObjectURL(img.blob);
      }
      thumb.appendChild(thumbImg);

      var removeBtn = document.createElement('button');
      removeBtn.className = 'remove-img';
      removeBtn.textContent = '\u00D7';
      removeBtn.addEventListener('click', function () {
        var idx = pendingImages.indexOf(img);
        if (idx !== -1) pendingImages.splice(idx, 1);
        thumb.remove();
      });
      thumb.appendChild(removeBtn);
      imagesEl.appendChild(thumb);
    });
  }

  function applyToolbarAction(textarea, action) {
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var selected = textarea.value.slice(start, end);
    var replacement, cursorOffset;

    switch (action) {
      case 'bold':
        replacement = '**' + (selected || 'bold text') + '**';
        cursorOffset = selected ? replacement.length : 2;
        break;
      case 'italic':
        replacement = '*' + (selected || 'italic text') + '*';
        cursorOffset = selected ? replacement.length : 1;
        break;
      case 'heading':
        replacement = '## ' + (selected || 'Heading');
        cursorOffset = replacement.length;
        break;
      case 'link':
        if (selected) {
          replacement = '[' + selected + '](url)';
          cursorOffset = replacement.length - 4;
        } else {
          replacement = '[link text](url)';
          cursorOffset = 1;
        }
        break;
      case 'hr':
        replacement = '\n---\n';
        cursorOffset = replacement.length;
        break;
      default:
        return;
    }

    var before = textarea.value.slice(0, start);
    var after = textarea.value.slice(end);
    textarea.value = before + replacement + after;
    textarea.selectionStart = textarea.selectionEnd = start + cursorOffset;
    textarea.focus();
  }

  // ── 13. Post Page Edit Controls ───────────────────────────────────────────

  function addPostPageControls() {
    var h1 = document.querySelector('article h1');
    if (!h1 || h1.querySelector('.edit-post-btn')) return;

    var editBtn = document.createElement('button');
    editBtn.className = 'edit-post-btn edit-only';
    editBtn.title = 'Edit this post';
    editBtn.innerHTML = '&#9998;';
    editBtn.addEventListener('click', function () {
      var urlSlug = getUrlSlug();
      var stem = urlSlugToFileStem(urlSlug);
      if (!stem) { showToast('Cannot determine file for this post', 'error'); return; }
      openEditor({ path: 'blog/' + stem + '.md', isDraft: false });
    });
    h1.appendChild(editBtn);
  }

  // ── 14. Index Page Controls ───────────────────────────────────────────────

  function addIndexPageControls() {
    if (!isIndexPage || !postList) return;

    // New Post button
    if (!document.querySelector('.new-post-btn')) {
      var newBtn = document.createElement('button');
      newBtn.className = 'new-post-btn edit-only';
      newBtn.innerHTML = '+ New Post';
      newBtn.addEventListener('click', function () {
        openEditor({ path: null, isDraft: false });
      });
      postList.parentNode.insertBefore(newBtn, postList);
    }

    // Edit icons on existing post items
    var items = postList.querySelectorAll('li:not(.draft-item)');
    items.forEach(function (li) {
      if (li.querySelector('.edit-item-btn')) return;
      var link = li.querySelector('a');
      if (!link) return;
      var href = link.getAttribute('href');
      if (!href) return;

      var editBtn = document.createElement('button');
      editBtn.className = 'edit-item-btn edit-only';
      editBtn.title = 'Edit';
      editBtn.innerHTML = '&#9998;';
      editBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var slug = href.replace(/\/$/, '').split('/').pop();
        var stem = urlSlugToFileStem(slug);
        if (!stem) { showToast('Cannot determine file path', 'error'); return; }
        openEditor({ path: 'blog/' + stem + '.md', isDraft: false });
      });

      var titleSpan = li.querySelector('.post-title');
      if (titleSpan) {
        titleSpan.appendChild(editBtn);
      }
    });
  }

  // ── 15. Utilities ─────────────────────────────────────────────────────────

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── 16. Activate Edit Mode ────────────────────────────────────────────────

  function activateEditMode() {
    document.body.classList.add('edit-mode');
    showToast('Edit mode active', 'success');

    if (isPostPage) addPostPageControls();
    if (isIndexPage) {
      addIndexPageControls();
      loadDraftsOnIndex();
    }
  }

  // ── 17. Init ──────────────────────────────────────────────────────────────

  setupLockButton();

  if (isAuthenticated()) {
    activateEditMode();
  }
})();
