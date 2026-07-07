# Movies editor: local-first edit queue + fold-state preservation

Date: 2026-07-06

## Problem

The static movies viewer (`movies/index.html`) has an inline editor overlay
(`movies/edit-online.js`) that commits every edit to GitHub **synchronously and
immediately**, one commit + push per edit. This causes three problems:

1. **Lost place / folded lists.** After a save, `window.__refreshMoviesText`
   calls the viewer's `render()`, which rebuilds `#content` from scratch. Open
   state for sections/subsections and expanded cards lives only as a DOM `.open`
   class, so every save collapses the whole tree and the user has to find their
   place again.

2. **"Cannot fast-forward" conflicts.** Each edit's push triggers the
   `enrich-movies.yml` workflow, which does a plain `git push`. Two edits in
   quick succession produce: push A -> workflow run 1 starts on A -> push B lands
   -> workflow run 1 finishes and tries to push a cleanup commit whose parent is
   A, but the tip is now B -> non-fast-forward, the Action fails. The browser's
   `createCommit` retry-on-422 only protects the *browser's* push, not the
   *workflow's*.

3. **Durability worry.** With synchronous commits there is no local buffer, and
   the user wants to make several edits that queue up, survive a browser close,
   and push in the background, while showing as applied in the viewer
   immediately.

## Goal

Move the viewer's editor to a **local-first** model: edits mutate a local copy of
`movies.log`, render optimistically, persist to IndexedDB (surviving a browser
close), and drain to GitHub as a single coalesced background commit. Preserve the
list's expand/collapse state across re-renders. Harden the enrichment workflow so
it can never fail with a non-fast-forward.

## Non-goals

- No refactor of the working `movie-writer` PWA (it already works this way).
- No `navigator.storage.persist()` request (user opted out; rely on fast sync +
  exit guard instead).
- No visible, individually-cancelable queue UI. A single status badge is enough.
- No change to the parser, route/mutation helpers, or the data format.

## Approach

Reuse the PWA's existing local-first primitives from
`movie-writer/js/storage.js` (IndexedDB store with `moviesText`, `dirty`,
`pendingMessages`). Route the viewer's edits through that queue instead of
committing synchronously. This is the smallest change that meets the need and
reuses code already trusted in production.

## Components & changes

### 1. `movie-writer/js/storage.js` — reused, unchanged

Provides: `getLocalMovies` / `setLocalMovies`, `isDirty` / `setDirty`,
`getPendingMessages` / `addPendingMessage` / `clearPendingMessages`. Same
IndexedDB database (`movie-writer`) the PWA uses, so the viewer and PWA share one
queue and one local canonical text.

### 2. `movies/edit-online.js` — sync path rewritten

- Import `storage.js`.
- Replace `pushAndRefresh(newText, message)` with a **local mutation**:
  `saveLocalAndRender(newText, message)` which:
  1. `await setLocalMovies(newText)`, `await setDirty(true)`,
     `await addPendingMessage(message)`.
  2. Update `window.__moviesText = newText` and call
     `window.__refreshMoviesText(newText)` for the optimistic viewer update.
  3. `updateSyncBadge()` and `scheduleSync()`.
- `scheduleSync()`: debounce ~1000 ms, then `doSync()`.
- `doSync()`:
  - Reentrancy guard; bail if not dirty.
  - Coalesce `pendingMessages` into one message (first few joined, "+N more").
  - `await createCommit([{ path: 'movies.log', content: <current local text> }], message)`.
  - On success: `setDirty(false)`, `clearPendingMessages()`, then best-effort
    refetch of `movies.log` from GitHub and `__refreshMoviesText` to pull in the
    enrichment workflow's cleanup.
  - On failure: leave dirty + pending; log; badge shows `pending`. Retried on
    next edit, on `visibilitychange` (tab refocus), on `online`, and on load.
- The existing `pollForEnrichment` behavior is superseded by the
  refetch-after-sync step; remove it (the post-sync refetch already pulls the
  workflow result once it lands, and a single refetch on the next sync/refocus
  keeps things current without a 90s polling loop).
- `commitEdit`, `commitDelete`, `commitAdd`, `applyImdbDetails` all now end by
  calling `saveLocalAndRender` instead of `pushAndRefresh`. Their in-memory text
  mutation logic is unchanged.

### 3. `movies/index.html` — load reconciliation, badge, exit guard, fold state

**Load reconciliation** (in `init`): to avoid a race where `init`'s remote fetch
clobbers unsynced local edits, reconciliation happens *inside* `init` before the
first render. `init` dynamically imports the storage module
(`const storage = await import('../movie-writer/js/storage.js')`), then:

```js
const remote = await fetchMoviesLog();
const dirty = await storage.isDirty();
const local = await storage.getLocalMovies();
const text = (dirty && local) ? local : remote;
window.__moviesText = text;
data = parseLog(text);
// ...existing render path...
```

If local (dirty) text is used, `init` also signals `edit-online.js` to show the
`pending` badge and schedule a sync (via a `window` flag or a small
`window.__moviesSyncBoot()` hook that `edit-online.js` defines). `edit-online.js`
owns the sync loop, badge updates, and exit guard; `index.html` owns only this
load-time text selection.

**Sync badge**: a small element in `#hdr` actions showing `pending` / `syncing` /
`synced`, updated by `edit-online.js`. Clicking it forces `doSync()`. Only shown
in edit mode (`body.edit-mode`).

**Exit guard**: `beforeunload` handler (registered by `edit-online.js`) that calls
`preventDefault()` / sets `returnValue` only while `isDirty()` cached flag is
true, producing the browser's "leave site?" prompt.

**Fold-state preservation** (fixes problem 1):
- Two module-level sets in the viewer script: `openSecs` (section paths) and
  `openMovs` (movie titles).
- `buildGroup(group, level, path)` gains a `path` argument; each section wrapper
  gets `dataset.path = <full path from root group name>`, and is given `.open` if
  `openSecs.has(path)`.
- `buildMovieEl(m)` sets `dataset.title = m.title` and adds `.open` if
  `openMovs.has(m.title)`.
- `toggleSec(el)` / `toggleMv(el)` update `openSecs` / `openMovs` from the
  toggled element's `dataset.path` / `dataset.title`.
- The search "Enter expands matching sections" handler also adds those sections'
  paths to `openSecs` so they persist.
- Result: after any `render()` (including the optimistic post-save one), every
  section/card returns to the exact open state it had. A moved item's destination
  section keeps its own prior state (stays closed if it was closed) -> **source
  has priority**; expanded cards stay open.

### 4. `.github/workflows/enrich-movies.yml` — hardening (defense in depth)

- Add:
  ```yaml
  concurrency:
    group: enrich-movies
    cancel-in-progress: true
  ```
  so a newer push cancels an in-flight, now-stale run instead of letting it push
  a conflicting commit. Safe because the workflow only runs deterministic,
  idempotent steps (`fix_recommenders.py`, `movie cleanup`), so a cancelled run
  loses nothing a later run won't redo.
- Set `fetch-depth: 0` on `actions/checkout` (needed for a clean rebase).
- Replace the plain `git push` with a rebase-retry loop:
  ```bash
  git commit -m "Auto-enrich movies with IMDb data"
  for attempt in 1 2 3 4 5; do
    git push && exit 0
    echo "Push rejected (attempt $attempt); rebasing onto latest main..."
    git pull --rebase origin main || true
  done
  echo "Failed to push after 5 attempts" >&2
  exit 1
  ```
  So even if the tip moved, the run reconciles and succeeds instead of erroring
  with "cannot fast-forward".

## Data flow

```
edit -> mutate local text -> IndexedDB (setLocalMovies/setDirty/addPendingMessage)
     -> optimistic __refreshMoviesText (fold state preserved) -> badge "pending"
     -> debounce ~1s -> doSync():
          createCommit(one commit, all pending) -> success:
              setDirty(false); clearPendingMessages()
              refetch movies.log from GitHub -> __refreshMoviesText -> badge "synced"
          failure: stay dirty/pending -> retry on edit / refocus / online / load

reload -> fetch remote; if dirty in IndexedDB, use local text instead + schedule sync
close  -> if dirty, beforeunload prompt
```

## Error handling

- **Push failure / offline:** queue persists; badge `pending`; retried on next
  edit, `visibilitychange`, `online`, and load. No data loss short of a manual
  site-data wipe while offline with edits pending.
- **Ref moved mid-push (single browser):** `createCommit`'s existing 3x retry on
  HTTP 422 handles it.
- **Workflow race:** concurrency + rebase-retry (see 4).
- **Enrichment overwrite:** the post-sync refetch pulls the workflow's cleanup
  into the local text; because syncs coalesce and refetch, the local copy
  converges to the enriched version rather than repeatedly clobbering it.

## Testing / verification

Drive the viewer locally (`scripts/serve.py`) with Playwright, stubbing
`createCommit` so no real push happens:

1. **Fold state:** open a section + expand a card, invoke
   `window.__refreshMoviesText(sameText)`, assert the section and card are still
   open (and that a *different*, previously-closed section is still closed).
2. **Optimistic + badge:** simulate an edit through `saveLocalAndRender`; assert
   the viewer shows the change immediately and the badge reads `pending`.
3. **Reload reconciliation:** with a dirty IndexedDB queue, reload and assert the
   local (unsynced) edit is what renders.

The workflow YAML change is verified by inspection (and, once merged, by watching
that concurrent edits no longer produce a failed Action).

## Files touched

- `movies/edit-online.js` (sync path -> local-first queue; boot reconciliation;
  badge + exit-guard wiring)
- `movies/index.html` (fold-state preservation; sync-badge element; small bridge
  for load reconciliation if needed)
- `.github/workflows/enrich-movies.yml` (concurrency + rebase-retry + fetch-depth)
- `movie-writer/js/storage.js` (reused, no change expected)
