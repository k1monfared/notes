/**
 * Generic loglog editor — pairs with shared/loglog-viewer.js.
 *
 * Adds a lock icon, login dialog, pencil button on each rendered item,
 * an edit modal that round-trips the entry's child block through the
 * loglog grammar, and "+" button to add new items. Saves go to GitHub
 * via the same `gh_token` localStorage key the blog/movies editors use.
 *
 * Per-page hookup:
 *
 *   <script src="../shared/loglog-viewer.js"></script>
 *   <script src="../shared/loglog-editor.js"></script>
 *   <script>
 *     const app = document.getElementById('app');
 *     createLoglogViewer(app, {...});
 *     createLoglogEditor(app, {
 *       dataFile: '../books.log',          // same path as viewer
 *       commitPrefix: 'books',             // e.g. "books: edit Foo"
 *       checkboxStates: ['', 'x', '-', '?'],  // optional cycle
 *       tiers: [...],                      // optional dropdown
 *       reviewKey: 'review',               // optional, default 'review'
 *     });
 *   </script>
 *
 * No domain-specific schema needed: the modal renders one row per
 * property the entry already has. Press "+ Add property" to create a
 * new key. Lines that aren't `key: value` (or `key:` with nested
 * children) become Notes — one per line in a textarea.
 */

(function () {
  'use strict';

  const TOKEN_KEY = 'gh_token';
  const REPO = 'k1monfared/notes';
  const API = 'https://api.github.com';

  // ── Auth ──────────────────────────────────────────────────────────────────

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const setToken = (t) => localStorage.setItem(TOKEN_KEY, t.trim());
  const clearToken = () => localStorage.removeItem(TOKEN_KEY);
  const isAuthed = () => !!getToken();

  async function validateToken(token) {
    try {
      const res = await fetch(`${API}/repos/${REPO}`, {
        headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github.v3+json' },
      });
      if (!res.ok) return { valid: false, error: `HTTP ${res.status}` };
      const data = await res.json();
      if (!data.permissions || !data.permissions.push) {
        return { valid: false, error: 'Token lacks write permission for this repo' };
      }
      return { valid: true };
    } catch (err) {
      return { valid: false, error: err.message };
    }
  }

  // ── GitHub commit (with 422-retry, like the blog/movies editors) ────────

  async function ghReq(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
        Accept: 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      ...options,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(`GitHub API ${res.status}: ${body.message || res.statusText}`);
    }
    return res.json();
  }

  async function getFile(path) {
    const data = await ghReq(`/repos/${REPO}/contents/${encodeURIComponent(path)}`);
    const raw = atob(data.content.replace(/\n/g, ''));
    const bytes = Uint8Array.from(raw, c => c.charCodeAt(0));
    const text = new TextDecoder().decode(bytes);
    return { content: text, sha: data.sha };
  }

  async function createCommit(files, message) {
    const refPath = `/repos/${REPO}/git/refs/heads/main`;
    for (let attempt = 0; attempt < 3; attempt++) {
      const ref = await ghReq(refPath);
      const baseSha = ref.object.sha;
      const baseCommit = await ghReq(`/repos/${REPO}/git/commits/${baseSha}`);
      const baseTreeSha = baseCommit.tree.sha;
      const treeItems = [];
      for (const f of files) {
        const blob = await ghReq(`/repos/${REPO}/git/blobs`, {
          method: 'POST',
          body: JSON.stringify({ content: f.content, encoding: f.encoding || 'utf-8' }),
        });
        treeItems.push({ path: f.path, mode: '100644', type: 'blob', sha: blob.sha });
      }
      const tree = await ghReq(`/repos/${REPO}/git/trees`, {
        method: 'POST',
        body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems }),
      });
      const commit = await ghReq(`/repos/${REPO}/git/commits`, {
        method: 'POST',
        body: JSON.stringify({ message, tree: tree.sha, parents: [baseSha] }),
      });
      try {
        await ghReq(refPath, { method: 'PATCH', body: JSON.stringify({ sha: commit.sha }) });
        return commit;
      } catch (err) {
        if (err.message.includes('422') && attempt < 2) continue;
        throw err;
      }
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  const esc = (s) => {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  };

  const splitLines = (text) =>
    text.split('\n').map((l, i, a) => i < a.length - 1 ? l + '\n' : (l ? l + '\n' : ''));

  const joinLines = (lines) => lines.join('').replace(/\n$/, '');

  // ── Block parser/serializer (loglog grammar around one item's children) ──

  // A "block" is a model of an item's child lines:
  //   { fields: [{ key, value, multi }, ...], notes: [string, ...] }
  //
  //   - "field": a child line that looks like `- key: value` or `- key:` with
  //     indented sub-bullets. value is the joined text (possibly multi-line).
  //     `multi` is true when the value originated from indented children.
  //   - "note": a child line at the entry's prop indent that doesn't match
  //     a field shape (e.g. `- U.S.A.` or `- A nicely made musical love story.`).
  //
  // This mirrors how a human edits a `.log` file: short inline `key: value`
  // pairs, occasional `key:` blocks with nested values, and free-prose
  // bullets.

  // Match a key in the form "- key:" or "key:". Key allows letters, digits,
  // spaces, dashes, slashes, ampersands, parens, apostrophes — same set the
  // viewer uses, plus a permissive trailing colon.
  const FIELD_LINE_RE = /^-?\s*([A-Za-z][\w\s/&'()\-]*?):\s*(.*)$/;
  const URL_ONLY_RE = /^https?:\/\/[^\s]+$/;
  const SENTENCE_END = /[.,;:!?)\]]$/;
  const MAX_KEY_WORDS = 5;
  const MAX_KEY_CHARS = 40;

  // Pure-URL probe. Returns the URL string when the input is *exactly* a URL,
  // otherwise null. Trailing sentence punctuation kicks it out (ambiguous).
  function asPureUrl(text) {
    const t = (text || '').trim();
    return (URL_ONLY_RE.test(t) && !SENTENCE_END.test(t)) ? t : null;
  }

  // "Is this a clear field line?" probe. Returns { key, value } when the
  // input parses unambiguously as a structured field; otherwise null.
  // Rejection rules (everything else falls back to notes):
  //   - http/https as keys (those are URLs, not fields)
  //   - keys longer than 5 words or 40 chars (those are mid-sentence colons)
  function asClearField(text) {
    const inner = (text || '').replace(/^-\s*/, '').trim();
    if (!inner) return null;
    // Pure URL is a clear field too, classified as `url`
    const url = asPureUrl(inner);
    if (url) return { key: 'url', value: url };
    const m = inner.match(FIELD_LINE_RE);
    if (!m) return null;
    const key = m[1].trim();
    if (/^https?$/i.test(key)) return null;
    const wordCount = key.split(/\s+/).length;
    if (wordCount > MAX_KEY_WORDS || key.length > MAX_KEY_CHARS) return null;
    return { key, value: m[2].trim() };
  }

  function parseEntryBlock(lines, itemLineIdx, itemIndent) {
    // Walk children of the item until we hit a sibling/parent.
    const propIndent = itemIndent + 4;
    const fields = [];
    const notes = [];
    let i = itemLineIdx + 1;

    while (i < lines.length) {
      const raw = lines[i];
      const stripped = raw.replace(/\n$/, '');
      if (!stripped.trim()) { i++; continue; }
      const ind = stripped.search(/\S/);
      if (ind <= itemIndent) break;          // left the entry
      if (ind !== propIndent) {              // deeper than prop indent → treat as part of the previous field's value
        i++; continue;
      }

      const inner = stripped.replace(/^\s*-\s*/, '').replace(/^\s*/, '');
      const startedWithDash = /^\s*-\s/.test(stripped);

      // Look ahead for nested-value bullets (deeper than propIndent)
      const nestedLines = [];
      let j = i + 1;
      while (j < lines.length) {
        const r2 = lines[j].replace(/\n$/, '');
        if (!r2.trim()) { j++; continue; }
        const ind2 = r2.search(/\S/);
        if (ind2 <= propIndent) break;
        nestedLines.push(r2.replace(/^\s*-?\s*/, ''));
        j++;
      }

      // 0. Pure-URL line ("- https://example.com") → `url` field.
      //    Strict: the WHOLE line content (after the leading dash) must be
      //    exactly one URL with no whitespace and no sentence-end punctuation.
      //    Anything ambiguous (trailing prose, trailing period, etc.) falls
      //    through to the note path.
      const trimmedInner = inner.trim();
      if (startedWithDash && nestedLines.length === 0) {
        const url = asPureUrl(trimmedInner);
        if (url) {
          fields.push({ key: 'url', value: url, multi: false });
          i++;
          continue;
        }
      }

      // 1. "- key: value" / "- key:" → field, but only when the key passes
      //    the asClearField sanity test (short, not http/https, etc.).
      //    Anything ambiguous falls through to the note path.
      if (startedWithDash) {
        // Treat colon-ending "- key:" with nested children as a multi-line
        // field even when there's no inline value.
        const m = inner.match(FIELD_LINE_RE);
        if (m) {
          const key = m[1].trim();
          const inlineVal = m[2].trim();
          const looksLikeKey = !/^https?$/i.test(key)
            && key.split(/\s+/).length <= MAX_KEY_WORDS
            && key.length <= MAX_KEY_CHARS;
          if (looksLikeKey) {
            if (inlineVal && nestedLines.length === 0) {
              fields.push({ key, value: inlineVal, multi: false });
            } else if (!inlineVal && nestedLines.length > 0) {
              fields.push({ key, value: nestedLines.join('\n'), multi: true });
            } else if (inlineVal && nestedLines.length > 0) {
              fields.push({ key, value: [inlineVal, ...nestedLines].join('\n'), multi: true });
            } else {
              fields.push({ key, value: '', multi: false });
            }
            i = j;
            continue;
          }
        }
      }

      // 2. "- key" (no colon) + nested children → treat as key with multi-line
      //    value. Heuristic: key is short (≤5 words, ≤40 chars), no special
      //    characters except dashes/spaces. Avoids treating long prose like
      //    "- A nicely made musical love story" as a key.
      if (startedWithDash && nestedLines.length > 0) {
        const trimmedInner = inner.trim();
        const wordCount = trimmedInner.split(/\s+/).length;
        const looksLikeKey = wordCount <= 5 && trimmedInner.length <= 40 && /^[A-Za-z][\w\s/&'()\-]*$/.test(trimmedInner);
        if (looksLikeKey) {
          fields.push({ key: trimmedInner, value: nestedLines.join('\n'), multi: true });
          i = j;
          continue;
        }
      }

      // 3. Free-prose note
      if (startedWithDash) {
        notes.push(inner);
      } else {
        notes.push(stripped.trim());
      }
      i++;
    }
    return { fields, notes, endIdx: i };
  }

  function serializeBlock(block, itemIndent) {
    const propPad = ' '.repeat(itemIndent + 4);
    const deepPad = ' '.repeat(itemIndent + 8);
    const out = [];
    function emitField(key, value) {
      const lines = (value || '').replace(/\r/g, '').split('\n').map(s => s.trim()).filter(Boolean);
      if (lines.length === 0) {
        out.push(`${propPad}- ${key}:\n`);
      } else if (lines.length === 1) {
        out.push(`${propPad}- ${key}: ${lines[0]}\n`);
      } else {
        out.push(`${propPad}- ${key}:\n`);
        for (const ln of lines) out.push(`${deepPad}- ${ln}\n`);
      }
    }
    for (const f of block.fields) {
      const key = (f.key || '').trim();
      if (!key) continue;
      emitField(key, f.value);
    }
    // Notes pass: each note line is rechecked. If it now parses as a clear
    // field (e.g., the user moved a URL onto its own line as `url: http://…`,
    // or wrote `author: …`), promote it back into a field so the file ends
    // up with the structured form. Otherwise it stays as a free-prose note.
    for (const n of block.notes || []) {
      const text = (n || '').trim();
      if (!text) continue;
      const promoted = asClearField(text);
      if (promoted) emitField(promoted.key, promoted.value);
      else out.push(`${propPad}- ${text}\n`);
    }
    return out;
  }

  // Replace an entry's child block in `lines` with new block lines.
  function replaceEntryBlock(lines, itemLineIdx, itemIndent, newBlockLines) {
    const propIndent = itemIndent + 4;
    let endIdx = itemLineIdx + 1;
    while (endIdx < lines.length) {
      const r = lines[endIdx].replace(/\n$/, '');
      if (!r.trim()) { endIdx++; continue; }
      if (r.search(/\S/) <= itemIndent) break;
      endIdx++;
    }
    lines.splice(itemLineIdx + 1, endIdx - itemLineIdx - 1, ...newBlockLines);
    return lines;
  }

  // Update the title (and optional checkbox) on the item line itself.
  function rewriteItemLine(lines, itemLineIdx, itemIndent, newName, newCheckbox) {
    const pad = ' '.repeat(itemIndent);
    let prefix = '';
    if (newCheckbox !== undefined && newCheckbox !== null) {
      const ch = newCheckbox === 'x' ? '[x]' : newCheckbox === '-' ? '[-]' : newCheckbox === '?' ? '[?]' : '[]';
      prefix = `${pad}${ch} `;
    } else {
      // Preserve the existing prefix shape: "- Foo" or "[x] Foo" or bare "Foo"
      const orig = lines[itemLineIdx].replace(/\n$/, '');
      const cb = orig.match(/^\s*\[([x \-?]?)\]/i);
      if (cb) {
        prefix = `${pad}[${cb[1] || ' '}] `;
      } else if (/^\s*-\s/.test(orig)) {
        prefix = `${pad}- `;
      } else {
        prefix = pad;
      }
    }
    lines[itemLineIdx] = `${prefix}${newName}\n`;
    return lines;
  }

  // ── Modals (login + edit + add + confirm) ────────────────────────────────

  function makeOverlay() {
    const o = document.createElement('div');
    o.className = 'editor-dialog-overlay';
    document.body.appendChild(o);
    o.addEventListener('click', e => { if (e.target === o) o.remove(); });
    return o;
  }

  function showLoginDialog(onSuccess) {
    const o = makeOverlay();
    o.innerHTML = `
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
      </div>`;
    const input = o.querySelector('#login-token');
    const errEl = o.querySelector('#login-error');
    const connect = o.querySelector('#login-connect');
    input.focus();
    o.querySelector('.btn-cancel').addEventListener('click', () => o.remove());
    connect.addEventListener('click', async () => {
      const tok = input.value.trim();
      if (!tok) { errEl.textContent = 'Please enter a token.'; return; }
      connect.disabled = true; connect.textContent = 'Validating…';
      const r = await validateToken(tok);
      if (r.valid) { setToken(tok); o.remove(); onSuccess && onSuccess(); }
      else { errEl.textContent = r.error; connect.disabled = false; connect.textContent = 'Connect'; }
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') connect.click(); });
  }

  // ── Toast ────────────────────────────────────────────────────────────────

  let toastEl = null, toastTimer = null;
  function showToast(msg, type = 'info') {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'editor-toast'; document.body.appendChild(toastEl); }
    clearTimeout(toastTimer);
    toastEl.textContent = msg;
    toastEl.className = `editor-toast toast-${type} visible`;
    toastEl.onclick = () => toastEl.classList.remove('visible');
    if (type !== 'error') toastTimer = setTimeout(() => toastEl.classList.remove('visible'), 2500);
  }

  // ── Main public entry point ──────────────────────────────────────────────

  function createLoglogEditor(container, editorConfig) {
    const cfg = Object.assign({
      dataFile: null,
      commitPrefix: '',
      checkboxStates: null,        // e.g., ['', 'x', '-', '?']; null = no cycle
      reviewKey: 'review',
    }, editorConfig || {});

    // Add a lock + plus button to the viewer's title row (created by the
    // viewer in its <div id="hdr">).
    const hdrActions = container.querySelector('.title-row .hdr-actions');
    if (!hdrActions) {
      console.warn('loglog-editor: viewer title row missing — abort');
      return;
    }
    // Append (not replace) so any pre-existing buttons (e.g. the viewer's
    // gear) stay in place. Order: gear (left, from viewer) → add → lock.
    hdrActions.insertAdjacentHTML('beforeend', `
      <button id="loglog-add" class="hdr-icon-btn edit-only" title="Add new item">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </button>
      <button id="loglog-lock" class="hdr-icon-btn" title="Edit mode">
        <svg class="lock-closed" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
        <svg class="lock-open" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 019.9-1"/></svg>
      </button>`);

    const lockBtn = hdrActions.querySelector('#loglog-lock');
    const addBtn = hdrActions.querySelector('#loglog-add');

    function applyEditMode() {
      document.body.classList.toggle('edit-mode', isAuthed());
      lockBtn.title = isAuthed() ? 'Disconnect from edit mode' : 'Sign in to edit';
      attachPencils();
    }

    lockBtn.addEventListener('click', () => {
      if (isAuthed()) {
        if (confirm('Disconnect from edit mode?')) {
          clearToken();
          applyEditMode();
          location.reload();
        }
      } else {
        showLoginDialog(() => { applyEditMode(); showToast('Edit mode active'); });
      }
    });

    addBtn.addEventListener('click', () => openAddDialog());

    // Re-attach pencils every time the viewer renders (initial + after save).
    container.addEventListener('loglog-rendered', () => attachPencils());

    const PENCIL_SVG = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>`;

    function attachPencils() {
      // Items
      container.querySelectorAll('.item').forEach(it => {
        if (it.querySelector('.item-edit-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'item-edit-btn edit-only';
        btn.title = 'Edit';
        btn.innerHTML = PENCIL_SVG;
        const hdr = it.querySelector('.item-hdr');
        if (hdr) hdr.appendChild(btn);
        btn.addEventListener('click', (e) => {
          e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
          const lineIdx = parseInt(it.dataset.lineIdx, 10);
          const indent = parseInt(it.dataset.indent, 10);
          const checkbox = it.dataset.checkbox;
          const name = it.querySelector('.item-name')?.textContent || '';
          openEditDialog({ lineIdx, indent, checkbox, name });
        }, true);
      });

      // Sections (and subsections — they share the .sec-hdr structure)
      container.querySelectorAll('.sec[data-kind="section"]').forEach(sc => {
        const hdr = sc.querySelector('.sec-hdr');
        if (!hdr || hdr.querySelector('.sec-edit-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'sec-edit-btn edit-only';
        btn.title = 'Edit section';
        btn.innerHTML = PENCIL_SVG;
        hdr.appendChild(btn);
        btn.addEventListener('click', (e) => {
          e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
          const lineIdx = parseInt(sc.dataset.lineIdx, 10);
          const indent = parseInt(sc.dataset.indent, 10);
          const name = sc.querySelector('.sec-title')?.textContent || '';
          openSectionEditDialog({ lineIdx, indent, name });
        }, true);
      });
    }

    // Init
    applyEditMode();
    attachPencils();

    // ── Edit dialog ──────────────────────────────────────────────────────

    function openEditDialog(itemRef) {
      const state = container.__loglogState;
      if (!state) { showToast('No data loaded yet', 'error'); return; }
      const lines = splitLines(state.text);
      const block = parseEntryBlock(lines, itemRef.lineIdx, itemRef.indent);

      const o = makeOverlay();
      const checkboxRow = (cfg.checkboxStates && itemRef.checkbox !== undefined)
        ? `<label>Status</label>
           <select id="ed-status">
             ${cfg.checkboxStates.map(s =>
               `<option value="${esc(s)}" ${s === itemRef.checkbox ? 'selected' : ''}>${esc(statusLabel(s))}</option>`
             ).join('')}
           </select>`
        : '';
      const tierRow = (cfg.tiers && cfg.tiers.length)
        ? `<label>Section</label>
           <select id="ed-tier">
             <option value="">(no change)</option>
             ${cfg.tiers.map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('')}
           </select>`
        : '';

      // Separate review & notes from other fields for prominent textareas
      const reviewKey = (cfg.reviewKey || 'review').toLowerCase();
      const reviewField = block.fields.find(f => f.key.toLowerCase() === reviewKey);
      const otherFields = block.fields.filter(f => f.key.toLowerCase() !== reviewKey);

      o.innerHTML = `
        <div class="editor-dialog editor-dialog-wide">
          <h3>Edit item</h3>
          <div class="dialog-grid">
            <label>Title</label>
            <input type="text" id="ed-name" value="${esc(itemRef.name)}">
            ${checkboxRow}
            ${tierRow}
            <label>Review</label>
            <textarea id="ed-review" rows="3" placeholder="(no review)">${esc(reviewField ? reviewField.value : '')}</textarea>
          </div>
          <div class="fields-block">
            <div class="fields-label">Fields</div>
            <div id="ed-fields" class="ed-fields"></div>
            <button class="btn-secondary btn-add-field" id="ed-add-field" type="button">+ Add field</button>
          </div>
          <div class="dialog-grid">
            <label>Notes</label>
            <textarea id="ed-notes" rows="4" placeholder="One note per line">${esc(block.notes.join('\n'))}</textarea>
          </div>
          <details class="raw-details">
            <summary>Edit raw loglog block</summary>
            <textarea id="ed-raw" rows="10" placeholder="Raw lines (without leading indent)">${esc(serializeBlock(block, 0).map(l => l.replace(/\n$/, '')).join('\n'))}</textarea>
            <p class="dialog-hint">When this textarea has content, it overrides the structured fields above on save.</p>
          </details>
          <div class="dialog-error" id="ed-error"></div>
          <div class="dialog-actions">
            <button class="btn-danger" id="ed-delete">Delete</button>
            <span style="flex:1"></span>
            <button class="btn-cancel" id="ed-cancel">Cancel</button>
            <button class="btn-primary" id="ed-save">Save</button>
          </div>
        </div>`;

      // Render field rows
      const fieldsEl = o.querySelector('#ed-fields');
      otherFields.forEach((f, idx) => fieldsEl.appendChild(makeFieldRow(f.key, f.value)));

      o.querySelector('#ed-add-field').addEventListener('click', (e) => {
        e.preventDefault();
        fieldsEl.appendChild(makeFieldRow('', ''));
      });

      o.querySelector('#ed-cancel').addEventListener('click', () => o.remove());
      o.querySelector('#ed-delete').addEventListener('click', () => {
        if (!confirm(`Delete "${itemRef.name}"?`)) return;
        commitDelete(itemRef).then(() => o.remove())
          .catch(err => o.querySelector('#ed-error').textContent = 'Delete failed: ' + err.message);
      });

      o.querySelector('#ed-save').addEventListener('click', async () => {
        const errEl = o.querySelector('#ed-error');
        const saveBtn = o.querySelector('#ed-save');
        const newName = o.querySelector('#ed-name').value.trim() || itemRef.name;
        const newCheckbox = cfg.checkboxStates ? o.querySelector('#ed-status').value : itemRef.checkbox;
        const newReview = o.querySelector('#ed-review').value.trim();
        const newNotes = o.querySelector('#ed-notes').value
          .split('\n').map(s => s.trim()).filter(Boolean);
        const rawOverride = o.querySelector('#ed-raw').value.trim();

        let newBlock;
        if (rawOverride) {
          // Raw mode: re-parse the user-provided block as if it were under
          // an empty item so we get the same {fields, notes} shape.
          const fakeText = `placeholder\n` + rawOverride.split('\n').map(l => `    ${l}`).join('\n');
          const fakeLines = splitLines(fakeText);
          newBlock = parseEntryBlock(fakeLines, 0, 0);
        } else {
          // Structured mode: rebuild block from the form
          const fields = [];
          if (newReview) fields.push({ key: cfg.reviewKey || 'review', value: newReview });
          fieldsEl.querySelectorAll('.field-row').forEach(row => {
            const key = row.querySelector('.field-key').value.trim();
            const val = row.querySelector('.field-value').value.trim();
            if (key) fields.push({ key, value: val });
          });
          newBlock = { fields, notes: newNotes };
        }

        saveBtn.disabled = true; saveBtn.textContent = 'Saving…';
        try {
          await commitEdit(itemRef, newName, newCheckbox, newBlock);
          o.remove();
        } catch (err) {
          errEl.textContent = 'Save failed: ' + err.message;
          saveBtn.disabled = false; saveBtn.textContent = 'Save';
        }
      });
    }

    function makeFieldRow(key, value) {
      const row = document.createElement('div');
      row.className = 'field-row';
      const isMulti = (value || '').includes('\n');
      row.innerHTML = `
        <input type="text" class="field-key" placeholder="key" value="${esc(key)}">
        ${isMulti
          ? `<textarea class="field-value" rows="2">${esc(value)}</textarea>`
          : `<input type="text" class="field-value" value="${esc(value)}">`}
        <button class="field-remove" type="button" title="Remove field">×</button>`;
      row.querySelector('.field-remove').addEventListener('click', () => row.remove());
      // Switch to textarea when newline is typed
      const valueEl = row.querySelector('.field-value');
      if (valueEl.tagName === 'INPUT') {
        valueEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            const ta = document.createElement('textarea');
            ta.className = 'field-value'; ta.rows = 2;
            ta.value = valueEl.value + '\n';
            valueEl.replaceWith(ta);
            ta.focus();
            ta.selectionStart = ta.selectionEnd = ta.value.length;
          }
        });
      }
      return row;
    }

    // ── Save flows ───────────────────────────────────────────────────────

    async function commitEdit(itemRef, newName, newCheckbox, newBlock) {
      const state = container.__loglogState;
      const lines = splitLines(state.text);
      rewriteItemLine(lines, itemRef.lineIdx, itemRef.indent, newName, newCheckbox);
      const newBlockLines = serializeBlock(newBlock, itemRef.indent);
      replaceEntryBlock(lines, itemRef.lineIdx, itemRef.indent, newBlockLines);
      const newText = joinLines(lines);
      const message = `${cfg.commitPrefix ? cfg.commitPrefix + ': ' : ''}edit ${newName}`;
      await createCommit([{ path: cfg.dataFile.replace(/^\.\//, '').replace(/^\.\.\//, '') || cfg.dataFile, content: newText }], message);
      state.text = newText;
      state.refresh(newText);
      showToast(`Saved ${newName}`);
    }

    async function commitDelete(itemRef) {
      const state = container.__loglogState;
      const lines = splitLines(state.text);
      // Find end-of-block, then remove the item line + its children
      let endIdx = itemRef.lineIdx + 1;
      while (endIdx < lines.length) {
        const r = lines[endIdx].replace(/\n$/, '');
        if (!r.trim()) { endIdx++; continue; }
        if (r.search(/\S/) <= itemRef.indent) break;
        endIdx++;
      }
      lines.splice(itemRef.lineIdx, endIdx - itemRef.lineIdx);
      const newText = joinLines(lines);
      const message = `${cfg.commitPrefix ? cfg.commitPrefix + ': ' : ''}delete ${itemRef.name}`;
      await createCommit([{ path: cfg.dataFile.replace(/^\.\//, '').replace(/^\.\.\//, '') || cfg.dataFile, content: newText }], message);
      state.text = newText;
      state.refresh(newText);
      showToast(`Deleted ${itemRef.name}`);
    }

    // ── Section edit dialog ──────────────────────────────────────────────

    function openSectionEditDialog(secRef) {
      const state = container.__loglogState;
      if (!state) { showToast('No data loaded yet', 'error'); return; }
      const o = makeOverlay();
      o.innerHTML = `
        <div class="editor-dialog">
          <h3>Rename section</h3>
          <div class="dialog-grid">
            <label>Name</label>
            <input type="text" id="sec-name" value="${esc(secRef.name)}">
          </div>
          <div class="dialog-error" id="sec-error"></div>
          <div class="dialog-actions">
            <button class="btn-cancel" id="sec-cancel">Cancel</button>
            <span style="flex:1"></span>
            <button class="btn-primary" id="sec-save">Save</button>
          </div>
        </div>`;
      o.querySelector('#sec-cancel').addEventListener('click', () => o.remove());
      o.querySelector('#sec-save').addEventListener('click', async () => {
        const errEl = o.querySelector('#sec-error');
        const saveBtn = o.querySelector('#sec-save');
        const newName = o.querySelector('#sec-name').value.trim() || secRef.name;
        saveBtn.disabled = true; saveBtn.textContent = 'Saving…';
        try {
          await commitSectionRename(secRef, newName);
          o.remove();
        } catch (err) {
          errEl.textContent = 'Save failed: ' + err.message;
          saveBtn.disabled = false; saveBtn.textContent = 'Save';
        }
      });
    }

    async function commitSectionRename(secRef, newName) {
      const state = container.__loglogState;
      const lines = splitLines(state.text);
      // Rewrite the section header line, preserving leading prefix (dash /
      // checkbox / bare) and any trailing colon shape from the original.
      const orig = lines[secRef.lineIdx].replace(/\n$/, '');
      const cb = orig.match(/^\s*\[([x \-?]?)\]/i);
      const pad = ' '.repeat(secRef.indent);
      let prefix;
      if (cb) prefix = `${pad}[${cb[1] || ' '}] `;
      else if (/^\s*-\s/.test(orig)) prefix = `${pad}- `;
      else prefix = pad;
      const hadColon = /:\s*$/.test(orig);
      lines[secRef.lineIdx] = `${prefix}${newName}${hadColon ? ':' : ''}\n`;

      const newText = joinLines(lines);
      const message = `${cfg.commitPrefix ? cfg.commitPrefix + ': ' : ''}rename section ${newName}`;
      await createCommit([{ path: cfg.dataFile.replace(/^\.\//, '').replace(/^\.\.\//, '') || cfg.dataFile, content: newText }], message);
      state.text = newText;
      state.refresh(newText);
      showToast(`Renamed to ${newName}`);
    }

    // ── Add dialog ───────────────────────────────────────────────────────

    function openAddDialog() {
      const o = makeOverlay();
      o.innerHTML = `
        <div class="editor-dialog">
          <h3>Add item</h3>
          <div class="dialog-grid">
            <label>Title *</label>
            <input type="text" id="add-name" autofocus>
            <label>Notes</label>
            <textarea id="add-notes" rows="4" placeholder="Optional, one note per line"></textarea>
          </div>
          <div class="dialog-error" id="add-error"></div>
          <div class="dialog-actions">
            <button class="btn-cancel">Cancel</button>
            <button class="btn-primary" id="add-save">Add</button>
          </div>
        </div>`;
      o.querySelector('.btn-cancel').addEventListener('click', () => o.remove());
      o.querySelector('#add-save').addEventListener('click', async () => {
        const errEl = o.querySelector('#add-error');
        const saveBtn = o.querySelector('#add-save');
        const name = o.querySelector('#add-name').value.trim();
        if (!name) { errEl.textContent = 'Title is required.'; return; }
        const notes = o.querySelector('#add-notes').value
          .split('\n').map(s => s.trim()).filter(Boolean);

        saveBtn.disabled = true; saveBtn.textContent = 'Adding…';
        try {
          await commitAdd(name, notes);
          o.remove();
        } catch (err) {
          errEl.textContent = 'Add failed: ' + err.message;
          saveBtn.disabled = false; saveBtn.textContent = 'Add';
        }
      });
    }

    async function commitAdd(name, notes) {
      const state = container.__loglogState;
      const lines = splitLines(state.text);
      // Append a top-level item to the end of the file with indent 0.
      // (Domain-specific routing/sectioning can be added per page later.)
      const block = serializeBlock({ fields: [], notes }, 0);
      const itemLine = `- ${name}\n`;
      // Ensure file ends with a newline before appending
      if (lines.length && !lines[lines.length - 1].endsWith('\n')) {
        lines[lines.length - 1] = lines[lines.length - 1] + '\n';
      }
      lines.push(itemLine, ...block);
      const newText = joinLines(lines);
      const message = `${cfg.commitPrefix ? cfg.commitPrefix + ': ' : ''}add ${name}`;
      await createCommit([{ path: cfg.dataFile.replace(/^\.\//, '').replace(/^\.\.\//, '') || cfg.dataFile, content: newText }], message);
      state.text = newText;
      state.refresh(newText);
      showToast(`Added ${name}`);
    }

    // ── Helpers ──────────────────────────────────────────────────────────

    function statusLabel(s) {
      return s === 'x' ? 'done/watched' : s === '-' ? 'skipped' : s === '?' ? 'uncertain' : '(none)';
    }
  }

  // Expose to global
  window.createLoglogEditor = createLoglogEditor;
})();
