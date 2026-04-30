// Auto-routing logic — JS port of `movies/movie route` Python stage.
//
// The editor calls these helpers after every property change so the entry's
// location in movies.log stays in sync with its status/review/category.
//
// Two pieces:
//   decideDestination(entry) — passive, returns where a movie should live
//     based on its status (and review presence) when the source location is
//     not a valid home. Used after status flips.
//   applyMove(lines, entry, targetSection, targetCategory) — performs the
//     move: extracts the block, re-indents, splices, consumes any "-"
//     placeholder line on first insert. Returns the new lines array.

import {
  findSectionEnd, extractBlock, reindentBlock, findToWatchInsert,
} from './movies.js';

const TODO_RE = /^(\s*)\[([x\-? ]?)\]\s*(.+?)\s*$/i;

const VALID_X_SECTIONS = new Set(['watched', 'to review']);
const VALID_DASH_SECTIONS = new Set(['skipped']);
// Sections from which an entry should be ejected back to To Watch when its
// status returns to unwatched/uncertain.
const ACTIVE_HOMES = new Set(['watched', 'to review', 'skipped']);

// Indent at which the entry's checkbox line lives in each destination.
const DESTINATION_INDENT = {
  'watched|to categorize': 8,
  'to review|':            4,
  'skipped|':              4,
};

function destKey(section, category) {
  return `${(section || '').toLowerCase()}|${(category || '').toLowerCase()}`;
}

// Decide where a movie *should* live given its current state. Returns
// { section, category, toWatchEject? } or null if no move is needed.
//
// Rules (matching the Python stage + the "back to To Watch" follow-up):
//   [x] outside watched/To review:
//     has review → ('watched', 'to categorize')
//     no review  → ('To review', null)
//   [-] outside Skipped → ('Skipped', null)
//   [] or [?] currently in watched / To review / Skipped → eject back to
//     'To Watch' (placement uses findToWatchInsert, honouring an existing
//     `Recommended by > <name>` subsection if the entry has a Recommender).
//   otherwise → null
export function decideDestination(entry) {
  const sec = (entry.section || '').toLowerCase();
  const status = entry.status;
  const hasReview = !!(entry.props && (entry.props.review || (entry.props.reviews && entry.props.reviews.length)));

  if (status === 'x' && !VALID_X_SECTIONS.has(sec)) {
    if (hasReview) return { section: 'watched', category: 'to categorize' };
    return { section: 'To review', category: null };
  }
  if (status === '-' && !VALID_DASH_SECTIONS.has(sec)) {
    return { section: 'Skipped', category: null };
  }
  if ((status === '' || status === '?') && ACTIVE_HOMES.has(sec)) {
    return { section: 'To Watch', category: null, toWatchEject: true };
  }
  return null;
}

// Derive a Recommender label from the entry's parent group context. Mirrors
// the Python stage's per-parent-type rules. Returns a string or null.
export function deriveRecommender(entry) {
  const sec = (entry.section || '').toLowerCase();
  if (sec !== 'to watch') return null;
  const cat = entry.category;
  const sub = entry.subsection;
  if (!cat) return null;

  const catLower = cat.toLowerCase();
  if (catLower === 'festivals' && sub) {
    return sub.replace(/\s+https?:\/\/\S*$/i, '').trim();
  }
  if (catLower === 'recommended by' && sub) return sub.trim();
  if (catLower.startsWith('because of the director') && sub) {
    const name = sub.split(',', 1)[0].trim();
    return `Director: ${name}`;
  }
  if (cat && !sub) return cat.trim();
  return null;
}

// Insert a Recommender line at top of the entry's child block (right after the
// checkbox line) if one is missing. Mutates `lines` in place. Returns true if
// a line was inserted, false if the entry already had a Recommender.
export function ensureRecommender(lines, entry, value) {
  // Look for any existing Recommender variant in the entry's children
  const blockStart = entry.lineIndex;
  const blockEnd = findEndOfBlock(lines, blockStart, entry.indent);
  for (let i = blockStart + 1; i < blockEnd; i++) {
    const s = lines[i].trim();
    if (/^-?\s*recomm(end(ed by)?|m?ender|ender)\s*:/i.test(s)) return false;
  }
  const pad = ' '.repeat(entry.indent + 4);
  lines.splice(blockStart + 1, 0, `${pad}- Recommender: ${value}\n`);
  return true;
}

function findEndOfBlock(lines, movieIdx, movieIndent) {
  let idx = movieIdx + 1;
  while (idx < lines.length) {
    const stripped = lines[idx].trimEnd();
    if (!stripped.trim()) { idx++; continue; }
    const ind = stripped.length - stripped.trimStart().length;
    if (ind <= movieIndent) break;
    idx++;
  }
  return idx;
}

// Move an entry's block to (targetSection, targetCategory). Returns the new
// lines array or null on failure (e.g. destination not found).
//
// Special case: `targetSection === 'To Watch'` uses `findToWatchInsert` so
// we honour the existing subsection structure (Recommended by > <name>).
export function applyMove(lines, entry, targetSection, targetCategory) {
  // 1. Extract the entry's block (checkbox line + child lines).
  const block = extractBlock(lines, entry.lineIndex, entry.indent);
  if (block.length === 0) return null;

  // 2. Cut the block from the source.
  const out = lines.slice();
  const blockEnd = entry.lineIndex + block.length;
  out.splice(entry.lineIndex, blockEnd - entry.lineIndex);

  // 3. To-Watch eject: pick the right subsection via findToWatchInsert.
  if ((targetSection || '').toLowerCase() === 'to watch') {
    // Use the entry's first recommender as the subsection key, if any.
    const recRaw = entry.props?.recommenders?.[0]
      || (entry.props?.recommender ? entry.props.recommender.split(';')[0].trim() : '');
    const insert = findToWatchInsert(out, recRaw || null);
    if (!insert) return null;
    let { index: insertIdx, indent: targetIndent, newLines } = insert;
    if (newLines) {
      for (const nl of newLines) out.splice(insertIdx++, 0, nl);
    }
    const reindented = reindentBlock(block, entry.indent, targetIndent);
    out.splice(insertIdx, 0, ...reindented);
    return out;
  }

  // 4. Standard destinations (watched > to categorize / To review / Skipped).
  const targetIndent = DESTINATION_INDENT[destKey(targetSection, targetCategory)] ?? 8;
  const reindented = reindentBlock(block, entry.indent, targetIndent);

  const dest = findSectionEnd(out, targetSection, targetCategory);
  if (!dest) return null;

  let { insertIdx, placeholderIdx } = dest;
  if (placeholderIdx !== null) {
    out.splice(placeholderIdx, 1);
    if (placeholderIdx < insertIdx) insertIdx--;
  }
  out.splice(insertIdx, 0, ...reindented);
  return out;
}

// One-shot: given an entry, route it if needed. Returns:
//   { lines: <new lines>, target: <{section, category}>, recommenderAdded }
//   or null if nothing changed.
export function autoRoute(lines, entry) {
  const target = decideDestination(entry);
  if (!target) return null;

  // Inject Recommender if missing and we know how to derive one
  let workingLines = lines;
  let recommenderAdded = false;
  if (!entry.props || !(entry.props.recommender || (entry.props.recommenders && entry.props.recommenders.length))) {
    const derived = deriveRecommender(entry);
    if (derived) {
      // Mutate a clone so we don't disturb the caller's view
      workingLines = lines.slice();
      ensureRecommender(workingLines, entry, derived);
      recommenderAdded = true;
    }
  }

  // Re-extract a fresh entry shape against the (possibly mutated) lines so
  // applyMove sees the recommender line.
  const out = applyMove(workingLines, entry, target.section, target.category);
  if (!out) return null;

  return { lines: out, target, recommenderAdded };
}
