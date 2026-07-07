# Movies Editor Local-First Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the static movies viewer's inline editor local-first: edits queue in IndexedDB, render optimistically, survive a browser close, and drain to GitHub as one coalesced background commit; preserve list fold state across re-renders; and harden the enrichment workflow against non-fast-forward failures.

**Architecture:** Reuse the `movie-writer` PWA's existing IndexedDB primitives (`movie-writer/js/storage.js`) from the viewer's editor (`movies/edit-online.js`). Edits become local mutations that persist + render optimistically, then a debounced `doSync()` pushes one commit for all pending edits and refetches. The viewer (`movies/index.html`) preserves section/card open state across every render and picks local text on load when the queue is dirty. The GitHub Actions workflow gains concurrency + a rebase-retry push.

**Tech Stack:** Vanilla ES modules in the browser, IndexedDB (via `storage.js`), GitHub REST API (via `github.js`), GitHub Actions (bash), Playwright MCP for verification.

## Global Constraints

- Writing style (repo owner's rule): no em/en dashes or semicolons in prose/comments; use commas, colons, or periods.
- No emojis in UI. Text labels, SVG icons, or plain Unicode arrows only.
- Prefer FOSS. (No new dependencies needed here.)
- Do not modify `movie-writer/js/storage.js` (reused as-is) or the parser / route / mutation helpers.
- The same IndexedDB database name (`movie-writer`) is shared with the PWA, this is intentional (one queue).
- No `navigator.storage.persist()` request (durability = fast sync + `beforeunload` guard).
- Coalesce all pending edits into ONE commit per sync.
- Verification is Playwright-driven in-browser (no JS unit-test framework exists). Run the local server from the repo root: `python3 scripts/serve.py` (serves on `http://localhost:8787`, viewer at `/movies/`).

---

### Task 1: Preserve section/card fold state across re-renders

**Files:**
- Modify: `movies/index.html` (inline `<script>`: state globals, `buildGroup`, `buildMovieEl`, `render` call, `toggleSec`/`toggleMv`, search-Enter handler)

**Interfaces:**
- Consumes: nothing (self-contained viewer change).
- Produces: `window.__refreshMoviesText(text)` now returns a view whose section (`.sec`/`.subsec`) and card (`.mv`) open state matches whatever was open before. Section identity key = full path string `"<rootName> / <child> / ..."` on `dataset.path`; card identity key = movie title on `dataset.title`. Later tasks rely on this so optimistic re-renders keep the user's place.

- [ ] **Step 1: Add persistent open-state sets**

In `movies/index.html`, after the line `let reviewedFilter = 'all';  // 'all', 'yes', 'no'` add:

```javascript
// Expand/collapse state that must survive re-renders (optimistic edit saves,
// filter changes, tab switches). Sections are keyed by their full path from the
// tab's root group name, cards by movie title. Each element restores its own
// prior state, so a moved item's destination section keeps whatever state it
// had (source location has priority).
const openSecs = new Set();  // section paths currently expanded
const openMovs = new Set();  // movie titles currently expanded
```

- [ ] **Step 2: Tag movie cards with a stable key and restore open state**

In `buildMovieEl(m)`, immediately after `div.dataset.mid = id;` add:

```javascript
  div.dataset.title = m.title;
  if (openMovs.has(m.title)) div.classList.add('open');
```

- [ ] **Step 3: Thread a path through `buildGroup`, tag sections, restore open state**

Change the signature `function buildGroup(group, level) {` to:

```javascript
function buildGroup(group, level, path) {
```

At the top of the function, right after `if (!total) return null;`, add:

```javascript
  const myPath = path == null ? group.name : path;
```

In the `level === 0` branch, change the child recursion line
`const el = buildGroup(child, 1);` to:

```javascript
      const el = buildGroup(child, 1, myPath + ' / ' + child.name);
```

After `wrap.className = wrapClass;` (and the `if (t) wrap.dataset.t = t;` line), add:

```javascript
  wrap.dataset.path = myPath;
  if (openSecs.has(myPath)) wrap.classList.add('open');
```

In the deeper child recursion, change `const el = buildGroup(child, level + 1);` to:

```javascript
    const el = buildGroup(child, level + 1, myPath + ' / ' + child.name);
```

- [ ] **Step 4: Pass the root path in `render()`**

In `render()`, change `const frag = buildGroup(rootGroup, 0);` to:

```javascript
  const frag = buildGroup(rootGroup, 0, rootGroup.name);
```

- [ ] **Step 5: Make toggles update the persistent sets**

Replace:

```javascript
function toggleSec(el) { el.classList.toggle('open'); }
function toggleMv(el)  { el.classList.toggle('open'); }
```

with:

```javascript
function toggleSec(el) {
  const open = el.classList.toggle('open');
  const p = el.dataset.path;
  if (p) { if (open) openSecs.add(p); else openSecs.delete(p); }
}
function toggleMv(el) {
  const open = el.classList.toggle('open');
  const t = el.dataset.title;
  if (t) { if (open) openMovs.add(t); else openMovs.delete(t); }
}
```

- [ ] **Step 6: Persist sections opened by the search-Enter shortcut**

In the `searchEl.addEventListener('keydown', ...)` handler, replace:

```javascript
      document.querySelectorAll('.sec, .subsec').forEach(s => {
        if (s.querySelector('.mv')) s.classList.add('open');
      });
```

with:

```javascript
      document.querySelectorAll('.sec, .subsec').forEach(s => {
        if (s.querySelector('.mv')) {
          s.classList.add('open');
          if (s.dataset.path) openSecs.add(s.dataset.path);
        }
      });
```

- [ ] **Step 7: Verify fold state survives a re-render (Playwright)**

Start the server (background): `python3 scripts/serve.py` from the repo root.

Navigate to `http://localhost:8787/movies/`. Then run this in `browser_evaluate` and confirm it returns `{ movedOpenStayedOpen: true, otherStayedClosed: true }`:

```javascript
() => {
  const secs = [...document.querySelectorAll('.sec')];
  if (secs.length < 2) return { error: 'need >=2 sections; pick a tab with sections' };
  // Open the first section, leave the second closed.
  toggleSec(secs[0]);
  const openedPath = secs[0].dataset.path;
  const closedPath = secs[1].dataset.path;
  // Re-render with identical text (simulates an optimistic save).
  window.__refreshMoviesText(window.__moviesText);
  const opened = document.querySelector(`.sec[data-path="${CSS.escape(openedPath)}"]`);
  const closed = document.querySelector(`.sec[data-path="${CSS.escape(closedPath)}"]`);
  return {
    movedOpenStayedOpen: !!opened && opened.classList.contains('open'),
    otherStayedClosed: !!closed && !closed.classList.contains('open'),
  };
}
```

Expected: both booleans `true` (opened section stays open, other stays closed). If a tab has no sections (e.g. the default), switch tabs first by clicking a tab that does, or re-run after opening one.

- [ ] **Step 8: Commit**

```bash
git add movies/index.html
git commit -m "Preserve section/card fold state across viewer re-renders"
```

---

### Task 2: Local-first edit queue, optimistic sync, badge, exit guard

**Files:**
- Modify: `movies/edit-online.js` (imports; sync state + functions; replace `pushAndRefresh`; remove `pollForEnrichment`; badge; exit guard; boot)
- Modify: `movies/index.html` (`<style>`: sync-badge styling only)

**Interfaces:**
- Consumes: `storage.js` exports `getLocalMovies`, `setLocalMovies`, `isDirty`, `setDirty`, `addPendingMessage`, `getPendingMessages`, `clearPendingMessages`; `github.js` `createCommit(files, message)` and `getFile(path)`; `window.__refreshMoviesText(text)` (fold-preserving, from Task 1); `window.__moviesText`.
- Produces: `saveLocalAndRender(newText, message)` (async) as the single edit-commit entry point; a `#sync-badge` element in the header with `dataset.state` in `{pending, syncing, synced}`; `doSync()` (async) callable from the badge. Task 3 relies on `storage.isDirty()`/`getLocalMovies()` being written by this task's queue.

- [ ] **Step 1: Import the storage primitives**

In `movies/edit-online.js`, after the existing `import { isAuthenticated, ... } from '../movie-writer/js/auth.js';` block, add:

```javascript
import {
  getLocalMovies, setLocalMovies,
  isDirty, setDirty,
  addPendingMessage, getPendingMessages, clearPendingMessages,
} from '../movie-writer/js/storage.js';
```

- [ ] **Step 2: Add sync state next to the existing `let saving = false;`**

Replace `let saving = false;` with:

```javascript
let saving = false;
let syncTimer = null;     // debounce handle for scheduleSync
let syncing = false;      // reentrancy guard for doSync
let dirtyCache = false;   // in-memory mirror of storage.isDirty() for sync UI + exit guard
```

- [ ] **Step 3: Add the local-first sync engine**

Add this block just above the `// ── Mutation + commit ──` section header:

```javascript
// ── Local-first queue + background sync ──────────────────────────────────────

// Persist an edit locally, render it optimistically, and schedule a background
// push. Edits accumulate in IndexedDB (surviving a browser close) and drain to
// GitHub as a single coalesced commit.
async function saveLocalAndRender(newText, message) {
  window.__moviesText = newText;
  await setLocalMovies(newText);
  await setDirty(true);
  await addPendingMessage(message);
  dirtyCache = true;
  window.__refreshMoviesText(newText);   // fold state preserved (Task 1)
  updateSyncBadge();
  scheduleSync();
}

function scheduleSync() {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = setTimeout(() => { doSync(); }, 1000);
}

async function doSync() {
  if (syncing) return;
  // The viewer may not have populated window.__moviesText yet on boot; retry.
  if (!window.__moviesText) { scheduleSync(); return; }
  if (!(await isDirty())) { dirtyCache = false; updateSyncBadge(); return; }
  syncing = true;
  updateSyncBadge();
  try {
    const messages = await getPendingMessages();
    const message = messages.length <= 1
      ? (messages[0] || 'Update movies')
      : messages.slice(0, 5).join('; ') + (messages.length > 5 ? ` (+${messages.length - 5} more)` : '');

    await createCommit([{ path: 'movies.log', content: window.__moviesText }], message);

    await setDirty(false);
    await clearPendingMessages();
    dirtyCache = false;

    // Pull in anything the enrichment workflow committed on top of ours.
    // (Usually nothing yet, the workflow runs async; a later reload or sync
    // picks it up. Best-effort.)
    try {
      const file = await getFile('movies.log');
      if (file.content !== window.__moviesText) {
        window.__refreshMoviesText(file.content);
        await setLocalMovies(file.content);
      }
    } catch { /* refetch is best-effort */ }
  } catch (err) {
    console.error('Sync failed:', err);
    // Stays dirty + pending, retried on next edit, refocus, online, or load.
  } finally {
    syncing = false;
    updateSyncBadge();
  }
}

function updateSyncBadge() {
  const badge = document.getElementById('sync-badge');
  if (!badge) return;
  if (syncing) { badge.textContent = 'syncing…'; badge.dataset.state = 'syncing'; return; }
  badge.textContent = dirtyCache ? 'pending' : 'synced';
  badge.dataset.state = dirtyCache ? 'pending' : 'synced';
}
```

- [ ] **Step 4: Replace `pushAndRefresh` and delete `pollForEnrichment`**

Delete the entire `pushAndRefresh` function and the entire `pollForEnrichment` function (the block from `async function pushAndRefresh(newText, message) {` through the end of `pollForEnrichment`). Update every caller to use `saveLocalAndRender`:

- In `commitEdit`: change `await pushAndRefresh(newText, `Edit ${u.title}`);` to `await saveLocalAndRender(newText, `Edit ${u.title}`);`
- In `commitDelete`: change `await pushAndRefresh(joinLines(lines), `Delete ${title}`);` to `await saveLocalAndRender(joinLines(lines), `Delete ${title}`);`
- In `commitAdd`: change `await pushAndRefresh(joinLines(lines), `Add ${payload.title}`);` to `await saveLocalAndRender(joinLines(lines), `Add ${payload.title}`);`
- In `applyImdbDetails` (the `details.na` branch): change `await pushAndRefresh(joinLines(lines), `${originalTitle}: mark IMDb N/A`);` to `await saveLocalAndRender(joinLines(lines), `${originalTitle}: mark IMDb N/A`);`
- In `applyImdbDetails` (the normal branch): change `await pushAndRefresh(joinLines(lines), `Enrich ${originalTitle} from IMDb`);` to `await saveLocalAndRender(joinLines(lines), `Enrich ${originalTitle} from IMDb`);`

- [ ] **Step 5: Add badge setup, exit guard, and retry listeners; wire boot**

Replace the boot block at the end of the file:

```javascript
setupLockButton();
setupAddButton();
```

with:

```javascript
// ── Sync badge, exit guard, retry triggers ───────────────────────────────────

function setupSyncBadge() {
  const lock = document.getElementById('edit-lock');
  if (!lock || document.getElementById('sync-badge')) return;
  const badge = document.createElement('button');
  badge.id = 'sync-badge';
  badge.className = 'hdr-icon-btn edit-only';
  badge.title = 'Sync status, click to sync now';
  badge.textContent = 'synced';
  badge.dataset.state = 'synced';
  badge.addEventListener('click', () => doSync());
  lock.parentNode.insertBefore(badge, lock);
}

// Warn before leaving if edits are still queued (unsynced).
window.addEventListener('beforeunload', (e) => {
  if (dirtyCache) { e.preventDefault(); e.returnValue = ''; }
});

// Retry a pending queue when the tab regains focus or the network returns.
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && dirtyCache) scheduleSync();
});
window.addEventListener('online', () => { if (dirtyCache) scheduleSync(); });

// On boot, reflect any queue left over from a previous session and try to drain.
async function initQueueFromStorage() {
  try {
    dirtyCache = await isDirty();
    updateSyncBadge();
    if (dirtyCache) scheduleSync();
  } catch { /* storage unavailable */ }
}

setupLockButton();
setupAddButton();
setupSyncBadge();
initQueueFromStorage();
```

- [ ] **Step 6: Add sync-badge styling in `movies/index.html`**

In the `<style>` block of `movies/index.html`, right after the `body.edit-mode #edit-lock { color: var(--green); }` rule, add:

```css
#sync-badge {
  width: auto; padding: 3px 9px; font-size: 12px; border-radius: 6px;
  border: 1px solid var(--bd);
}
#sync-badge[data-state="pending"] { color: var(--ora); border-color: var(--ora); }
#sync-badge[data-state="syncing"] { color: var(--blue); border-color: var(--blue); }
#sync-badge[data-state="synced"]  { color: var(--txt2); }
```

- [ ] **Step 7: Verify optimistic edit + queue behavior (Playwright)**

With the server running, navigate to `http://localhost:8787/movies/`. Set a token and enter edit mode without a real push by stubbing the GitHub ref-update so `doSync` "succeeds" locally. Run this setup in `browser_evaluate`:

```javascript
() => {
  localStorage.setItem('gh_token', 'test-token');
  // Stub only GitHub API calls; leave /movies.log fetches alone.
  const realFetch = window.fetch.bind(window);
  window.fetch = (url, opts) => {
    const u = typeof url === 'string' ? url : url.url;
    if (u.startsWith('https://api.github.com')) {
      // Minimal happy-path shapes for github.js createCommit + getFile.
      const ok = (obj) => Promise.resolve(new Response(JSON.stringify(obj), { status: 200 }));
      if (u.includes('/git/refs/')) return ok({ object: { sha: 'base' } });
      if (u.includes('/git/commits/')) return ok({ tree: { sha: 'basetree' }, sha: 'base' });
      if (u.includes('/git/blobs')) return ok({ sha: 'blob' });
      if (u.includes('/git/trees')) return ok({ sha: 'tree' });
      if (u.includes('/git/commits')) return ok({ sha: 'newcommit' });
      if (u.includes('/contents/movies.log')) return ok({ content: btoa(unescape(encodeURIComponent(window.__moviesText))), sha: 'x', path: 'movies.log' });
      return ok({});
    }
    return realFetch(url, opts);
  };
  return 'stubbed';
}
```

Reload the page (so `body.edit-mode` is active from the token). Click a movie's edit pencil (`[data-action="edit-movie"]`), change Status to skipped, click Save. Then in `browser_evaluate` confirm the queue drained:

```javascript
async () => {
  const badge = document.getElementById('sync-badge');
  // Give the 1s debounce + async sync time before checking (poll up to 3s).
  for (let i = 0; i < 15 && badge.dataset.state !== 'synced'; i++) {
    await new Promise(r => setTimeout(r, 200));
  }
  return { badgeState: badge.dataset.state };
}
```

Expected: `badgeState: 'synced'` (edit was applied optimistically, queued, and the stubbed push drained the queue). Manually confirm the edited card's status icon changed in the list.

- [ ] **Step 8: Verify failure keeps the queue (Playwright)**

Reload without the success stub (real `gh_token` = `test-token` still set, so pushes 401). Edit a movie and Save, then in `browser_evaluate`:

```javascript
async () => {
  await new Promise(r => setTimeout(r, 2000)); // allow debounce + failed push
  const storage = await import('../movie-writer/js/storage.js');
  return { dirty: await storage.isDirty(), badge: document.getElementById('sync-badge').dataset.state };
}
```

Expected: `{ dirty: true, badge: 'pending' }` (failed push leaves the edit safely queued). Clean up afterward: `localStorage.removeItem('gh_token')` and clear the queue via `browser_evaluate`: `async () => { const s = await import('../movie-writer/js/storage.js'); await s.setDirty(false); await s.clearPendingMessages(); return 'cleared'; }`.

- [ ] **Step 9: Commit**

```bash
git add movies/edit-online.js movies/index.html
git commit -m "Route viewer edits through a local-first queued sync"
```

---

### Task 3: Load-time reconciliation (show local queue on reload)

**Files:**
- Modify: `movies/index.html` (`init()` only)

**Interfaces:**
- Consumes: `storage.isDirty()`, `storage.getLocalMovies()` (queue written by Task 2).
- Produces: on load, the viewer renders local (unsynced) text when the queue is dirty, otherwise remote, so a reload never appears to drop queued edits.

- [ ] **Step 1: Reconcile remote vs local queue in `init()`**

In `movies/index.html`, in `async function init()`, replace:

```javascript
    const text = await fetchMoviesLog();
    window.__moviesText = text;
    data = parseLog(text);
```

with:

```javascript
    const remote = await fetchMoviesLog();
    // If the local edit queue is dirty (unsynced edits from this or a prior
    // session), show those instead of remote so a reload never drops them.
    let text = remote;
    try {
      const storage = await import('../movie-writer/js/storage.js');
      if (await storage.isDirty()) {
        const local = await storage.getLocalMovies();
        if (local) text = local;
      }
    } catch { /* storage unavailable, fall back to remote */ }
    window.__moviesText = text;
    data = parseLog(text);
```

- [ ] **Step 2: Verify reload shows the queued edit (Playwright)**

With the server running and no real network needed, seed a dirty queue whose local text differs from remote, then reload and confirm the local text is what renders. In `browser_evaluate` at `http://localhost:8787/movies/`:

```javascript
async () => {
  const storage = await import('../movie-writer/js/storage.js');
  const marker = '[] __RELOAD_MARKER_MOVIE__';
  // Prepend a unique unwatched entry under the first tab's first group line.
  const text = window.__moviesText;
  const lines = text.split('\n');
  // Insert the marker as a top-level-ish entry we can search for after reload.
  const seeded = text + `\n- __reload_test__\n    ${marker}\n`;
  await storage.setLocalMovies(seeded);
  await storage.setDirty(true);
  return 'seeded';
}
```

Reload the page. Then in `browser_evaluate`:

```javascript
() => ({ hasMarker: window.__moviesText.includes('__RELOAD_MARKER_MOVIE__') })
```

Expected: `{ hasMarker: true }` (reload used the dirty local text, not remote). Clean up: `async () => { const s = await import('../movie-writer/js/storage.js'); await s.setDirty(false); await s.setLocalMovies(null); await s.clearPendingMessages(); return 'cleared'; }`, then reload once more to confirm remote text returns (`hasMarker: false`).

- [ ] **Step 3: Commit**

```bash
git add movies/index.html
git commit -m "Show local edit queue on viewer reload when dirty"
```

---

### Task 4: Harden the enrichment workflow against non-fast-forward

**Files:**
- Modify: `.github/workflows/enrich-movies.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: a workflow that cancels stale in-flight runs and rebase-retries its push, so a push landing during a run never fails the Action with "cannot fast-forward".

- [ ] **Step 1: Add a concurrency group**

In `.github/workflows/enrich-movies.yml`, after the `permissions:` block (before `jobs:`), add:

```yaml
concurrency:
  group: enrich-movies
  cancel-in-progress: true
```

- [ ] **Step 2: Deepen the checkout for a clean rebase**

Change the checkout step to fetch full history:

```yaml
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
```

- [ ] **Step 3: Replace the plain push with a rebase-retry loop**

Replace the `Commit enriched data` step's `run:` script with:

```yaml
      - name: Commit enriched data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add movies.log
          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi
          git commit -m "Auto-enrich movies with IMDb data"
          for attempt in 1 2 3 4 5; do
            if git push; then
              echo "Pushed on attempt $attempt"
              exit 0
            fi
            echo "Push rejected (attempt $attempt); rebasing onto latest main..."
            git pull --rebase origin main || true
          done
          echo "Failed to push after 5 attempts" >&2
          exit 1
```

- [ ] **Step 4: Verify the workflow is valid YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/enrich-movies.yml'))" && echo OK`
Expected: `OK` (no parse error). Also eyeball that `concurrency`, `fetch-depth: 0`, and the retry loop are present.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/enrich-movies.yml
git commit -m "Harden enrich-movies workflow with concurrency and rebase-retry push"
```

---

## Notes for the implementer

- The four tasks are independent deliverables and can be reviewed separately. Recommended order is 1 -> 2 -> 3 -> 4 (Task 2's optimistic render depends on Task 1's fold preservation for good UX; Task 3 reads the queue Task 2 writes).
- Template literals in the code blocks use backticks; keep them intact when editing `edit-online.js`.
- Do not "improve" unrelated code. Stay within the listed edits.
- After all tasks, do a final manual smoke test in a real browser with a real token if available: make two quick edits, confirm the badge goes pending -> synced with a single commit on GitHub, and that the enrichment Action run succeeds (no fast-forward error).
