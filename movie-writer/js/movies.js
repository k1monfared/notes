// Parse and modify movies.log.
//
// Single-source parser shared with the static viewer (movies/index.html).
// The data model is a recursive forest of Group nodes:
//
//     Group { name, indent, depth, movies: Movie[], children: Group[] }
//
// A Group can hold movies AND nested children. The top-level Groups are
// the root sections (`watched:`, `To review`, `Skipped`, `To Watch`); these
// become tabs in the UI. The viewer's parser does the same.
//
// The flat `movies` array is also returned so legacy callers (search,
// filters, find-by-title) can iterate without walking the tree.

const TODO_RE = /^(\s*)\[([x\-? ]?)\]\s*(.+?)\s*$/i;
const PROP_KEYS_RECOMMENDER = ['recommender', 'recommmender', 'receommender', 'recommended by'];

function isTodo(s) { return /^\[[x\-? ]?\]/i.test(s); }
function indentOf(s) { return s.length - s.trimStart().length; }

// ── Parser ───────────────────────────────────────────────────────────────────

export function parseMovies(text) {
  const lines = text.split('\n');
  const roots = [];
  const stack = [];   // Groups currently in scope, ordered by ascending indent.
  const movies = [];  // flat list, in source order

  let mov = null, movInd = -1, lastKey = null, collecting = null;

  function finishMov() { mov = null; movInd = -1; lastKey = null; collecting = null; }

  function popTo(indent) {
    while (stack.length && stack[stack.length - 1].indent >= indent) stack.pop();
  }

  function pushGroup(name, indent) {
    const parent = stack.length ? stack[stack.length - 1] : null;
    const g = {
      name, indent,
      depth: parent ? parent.depth + 1 : 0,
      movies: [], children: [],
    };
    if (parent) parent.children.push(g);
    else roots.push(g);
    stack.push(g);
    return g;
  }

  function setProp(rawKey, val) {
    if (!mov) return;
    const key = rawKey.toLowerCase().trim();
    const v = val.trim().replace(/\s*\(IMDb\)\s*$/, '');
    const p = mov.props;
    lastKey = key;
    collecting = null;

    if (key === 'imdb' || key === 'imdb link' || key === 'link') {
      if (!p.imdb && (v.startsWith('http') || v.toLowerCase() === 'n/a')) p.imdb = v;
    } else if (key === 'imdb rating' || (key === 'rating' && /\d+(\.\d+)?\s*\/\s*10/.test(v))) {
      p.rating = p.rating || v;
    } else if (key === 'year') {
      p.year = p.year || v;
    } else if (key === 'genres' || key === 'genre') {
      p.genres = p.genres || v;
    } else if (key === 'country') {
      p.country = p.country || v;
    } else if (key === 'duration') {
      p.duration = p.duration || v;
    } else if (key === 'released') {
      p.released = p.released || v;
    } else if (key === 'synopsis') {
      p.synopsis = p.synopsis || v;
      collecting = 'synopsis';
    } else if (key === 'director' || key === 'directors') {
      p.director = p.director ? p.director + ', ' + v : v;
      collecting = v ? null : 'director';
    } else if (key.startsWith('director and') || key.startsWith('directors and')) {
      // Multi-role keys preserved verbatim
      p.director = p.director ? p.director + ', ' + v : v;
    } else if (key === 'cast' || key === 'cast (imdb)') {
      if (!p.cast) p.cast = [];
      collecting = 'cast';
    } else if (PROP_KEYS_RECOMMENDER.includes(key)) {
      p.recommenders = p.recommenders || [];
      if (v) p.recommenders.push(v);
      // Backward-compat: also expose `recommender` as the joined value
      p.recommender = p.recommenders.join('; ');
    } else if (key === 'review') {
      if (v) {
        p.reviews = p.reviews || [];
        p.reviews.push(v);
        p.review = p.reviews.join(' — ');
      } else {
        collecting = 'review';
        p._pendingReview = '';
      }
    } else if (key === 'tag' || key === 'tags') {
      p.tags = (v ? v.split(',').map(s => s.trim()).filter(Boolean) : []);
    } else if (key === 'notes' || key === 'because of') {
      p.notes = (p.notes ? p.notes + '; ' : '') + v;
    }
  }

  function handleSubItem(inner) {
    if (!mov) return;
    const p = mov.props;
    const text = inner.trim();
    if (collecting === 'cast' || lastKey === 'cast' || lastKey === 'cast (imdb)') {
      if (!p.cast) p.cast = [];
      if (!text.includes(':')) p.cast.push(text);
    } else if (collecting === 'review') {
      if (p._pendingReview) p._pendingReview += ' ' + text;
      else p._pendingReview = text;
      // Commit accumulated review
      p.reviews = p.reviews || [];
      if (p.reviews.length === 0 || !p.reviews[p.reviews.length - 1].endsWith(p._pendingReview)) {
        // Replace the pending review with the latest accumulated form
        if (p.reviews.length === 0) p.reviews.push(p._pendingReview);
        else p.reviews[p.reviews.length - 1] = p._pendingReview;
      }
      p.review = p.reviews.join(' — ');
    } else if (collecting === 'director') {
      p.director = p.director ? p.director + ', ' + text : text;
    } else if (collecting === 'synopsis') {
      p.synopsis = p.synopsis ? p.synopsis + ' ' + text : text;
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const ind = indentOf(raw);
    const tr = raw.trim();
    if (!tr) continue;

    // Group header: "- name" at any indent, when not inside a movie's prop scope.
    if (tr.startsWith('- ') && !isTodo(tr.slice(2))) {
      if (mov && ind <= movInd) finishMov();
      if (!mov || ind <= movInd) {
        popTo(ind);
        const name = tr.slice(2).replace(/:\s*$/, '').trim();
        pushGroup(name, ind);
        continue;
      }
      // else: it's a property "- key: value" inside a movie scope → fall through
    }

    // Todo line → movie, attached to the deepest enclosing group.
    if (isTodo(tr)) {
      const m = TODO_RE.exec(raw);
      if (!m) continue;
      const indent = m[1].length;
      popTo(indent);
      const parent = stack.length ? stack[stack.length - 1] : null;
      if (!parent) continue;  // top-level [x] outside any group — skip

      const path = stack.map(g => g.name);
      mov = {
        lineIndex: i,
        indent,
        title: m[3].trim(),
        status: (m[2] || '').toLowerCase().trim(),
        rootSection: path[0] || '',
        section: path[0] || '',
        category: path[1] || null,
        subsection: path[2] || null,
        groupPath: path.slice(),
        props: {},
      };
      mov.watched = mov.status === 'x';
      movInd = indent;
      lastKey = null;
      collecting = null;
      parent.movies.push(mov);
      movies.push(mov);
      continue;
    }

    // Property of the current movie
    if (mov && ind > movInd) {
      const propInd = movInd + 4;
      let propText = tr;
      if (propText.startsWith('- ')) propText = propText.slice(2);

      if (ind === propInd) {
        const ci = propText.indexOf(':');
        if (ci > 0 && !propText.startsWith('http')) {
          setProp(propText.slice(0, ci), propText.slice(ci + 1));
        } else if (!tr.startsWith('- ')) {
          // Free-form line at prop indent (no colon): treat as a generic note
          if (propText.startsWith('http')) {
            mov.props.imdb = mov.props.imdb || propText;
          } else {
            mov.props.notes = (mov.props.notes ? mov.props.notes + '; ' : '') + propText;
          }
        } else {
          // "- text" with no colon → review/cast continuation if collecting, else note
          if (collecting === 'cast' || collecting === 'review' || collecting === 'director' || collecting === 'synopsis') {
            handleSubItem(propText);
          } else {
            mov.props.notes = (mov.props.notes ? mov.props.notes + '; ' : '') + propText;
          }
        }
      } else if (ind > propInd) {
        // Sub-bullet (cast member, multi-line review, etc.)
        if (tr.startsWith('- ')) handleSubItem(propText);
        else if (propText.includes(':')) {
          const ci = propText.indexOf(':');
          setProp(propText.slice(0, ci), propText.slice(ci + 1));
        }
      }
      continue;
    }
  }

  // Cleanup: strip the temporary _pendingReview marker
  for (const m of movies) {
    if (m.props._pendingReview !== undefined) delete m.props._pendingReview;
  }

  return { movies, roots };
}

// Walk every movie in a Group tree (depth-first, in source order).
export function* walkMovies(groups) {
  for (const g of groups) {
    for (const m of g.movies) yield m;
    yield* walkMovies(g.children);
  }
}

// ── Mutation helpers (used by app.js when applying edits) ────────────────────

// Find a movie line by title (case-insensitive). Returns { index, indent } or null.
export function findMovie(lines, title) {
  const titleLower = title.toLowerCase().trim();
  for (let i = 0; i < lines.length; i++) {
    const m = TODO_RE.exec(lines[i].trimEnd());
    if (m && m[3].trim().toLowerCase() === titleLower) {
      return { index: i, indent: m[1].length };
    }
  }
  return null;
}

// Find the index right after a movie's last child line.
export function findInsertAfter(lines, movieIdx, movieIndent) {
  let idx = movieIdx + 1;
  while (idx < lines.length) {
    const stripped = lines[idx].trimEnd();
    if (!stripped.trim()) { idx++; continue; }
    if (indentOf(stripped) <= movieIndent) break;
    idx++;
  }
  return idx;
}

// Get the full block of a movie (checkbox line + all child lines until indent <= movieIndent).
export function extractBlock(lines, movieIdx, movieIndent) {
  const end = findInsertAfter(lines, movieIdx, movieIndent);
  return lines.slice(movieIdx, end);
}

// Re-indent a block of lines by a delta number of spaces (positive or negative).
export function reindentBlock(blockLines, oldIndent, newIndent) {
  const delta = newIndent - oldIndent;
  if (delta === 0) return blockLines.slice();
  const out = [];
  for (const line of blockLines) {
    if (!line.trim()) { out.push(line); continue; }
    if (delta > 0) {
      out.push(' '.repeat(delta) + line);
    } else {
      const n = -delta;
      let j = 0;
      while (j < line.length && line[j] === ' ' && j < n) j++;
      out.push(line.slice(j));
    }
  }
  return out;
}

// Set the checkbox status on a movie line. status is one of 'x', '-', '?', '' (empty).
export function setStatus(lines, movieIdx, status) {
  const ch = status === 'x' ? '[x]' : status === '-' ? '[-]' : status === '?' ? '[?]' : '[]';
  lines[movieIdx] = lines[movieIdx].replace(/\[[x\-? ]?\]/i, ch);
  return lines;
}

// Add or update a review line on a movie.
export function setReview(lines, movieIdx, movieIndent, text) {
  const propPad = ' '.repeat(movieIndent + 4);
  const insertAt = findInsertAfter(lines, movieIdx, movieIndent);

  for (let i = movieIdx + 1; i < insertAt; i++) {
    const stripped = lines[i].trim();
    if (stripped.startsWith('- review:') || stripped.startsWith('review:')) {
      lines[i] = `${propPad}- review: ${text}\n`;
      // Drop multi-line review continuation
      let j = i + 1;
      while (j < lines.length) {
        const s = lines[j].trimEnd();
        if (!s.trim()) { j++; continue; }
        const ind = indentOf(s);
        if (ind >= movieIndent + 8 && s.trim().startsWith('- ')) {
          lines.splice(j, 1);
        } else break;
      }
      return lines;
    }
  }
  lines.splice(insertAt, 0, `${propPad}- review: ${text}\n`);
  return lines;
}

// Add or update a property line on a movie. If the property exists, it's replaced.
export function setProperty(lines, movieIdx, movieIndent, key, value) {
  const propPad = ' '.repeat(movieIndent + 4);
  const insertAt = findInsertAfter(lines, movieIdx, movieIndent);
  const keyLower = key.toLowerCase();

  for (let i = movieIdx + 1; i < insertAt; i++) {
    const stripped = lines[i].trim();
    let propContent = stripped;
    if (propContent.startsWith('- ')) propContent = propContent.slice(2);
    const colonIdx = propContent.indexOf(':');
    if (colonIdx > 0) {
      const existingKey = propContent.slice(0, colonIdx).trim().toLowerCase();
      if (existingKey === keyLower) {
        lines[i] = `${propPad}- ${key}: ${value}\n`;
        return lines;
      }
    }
  }
  lines.splice(insertAt, 0, `${propPad}- ${key}: ${value}\n`);
  return lines;
}

// Remove a property line from a movie (no-op if missing).
export function removeProperty(lines, movieIdx, movieIndent, key) {
  const insertAt = findInsertAfter(lines, movieIdx, movieIndent);
  const keyLower = key.toLowerCase();
  for (let i = movieIdx + 1; i < insertAt; i++) {
    const stripped = lines[i].trim();
    let propContent = stripped;
    if (propContent.startsWith('- ')) propContent = propContent.slice(2);
    const colonIdx = propContent.indexOf(':');
    if (colonIdx > 0) {
      const existingKey = propContent.slice(0, colonIdx).trim().toLowerCase();
      if (existingKey === keyLower) {
        lines.splice(i, 1);
        return lines;
      }
    }
  }
  return lines;
}

// Build a new movie entry block as lines.
export function buildMovieEntry(title, opts = {}, indent = 12) {
  const { recommender, director, year, review, tags } = opts;
  const pad = ' '.repeat(indent);
  const propPad = ' '.repeat(indent + 4);
  const out = [`${pad}[] ${title}\n`];
  if (recommender) out.push(`${propPad}- Recommender: ${recommender}\n`);
  if (director) out.push(`${propPad}- Director: ${director}\n`);
  if (year) out.push(`${propPad}- Year: ${year}\n`);
  if (review) out.push(`${propPad}- review: ${review}\n`);
  if (tags && tags.length) out.push(`${propPad}- tag: ${tags.join(', ')}\n`);
  return out;
}

// ── To Watch insertion (used by Add modal) ───────────────────────────────────

// Find the place to insert a new entry under "To Watch", optionally targeting a
// "Recommended by > <name>" subsection. If the recommender matches an existing
// subsection (case-insensitive), append there. Otherwise create one. Returns
// { index, indent, newLines } where newLines is an array of lines to splice in
// before the new entry (e.g. a fresh subsection header).
export function findToWatchInsert(lines, recommender) {
  let inToWatch = false;
  let recommendedByIdx = -1;
  let lastCatIdx = -1;
  let toWatchStart = -1;

  for (let i = 0; i < lines.length; i++) {
    const stripped = lines[i].trimEnd();
    if (!stripped.trim()) continue;
    const ind = indentOf(stripped);

    if (ind === 0) {
      if (inToWatch) break;
      if (stripped.trim().toLowerCase().replace(/[^a-z ]/g, '').includes('to watch')) {
        inToWatch = true;
        toWatchStart = i;
      }
      continue;
    }
    if (!inToWatch) continue;
    if (ind === 4 && stripped.trim().startsWith('- ')) {
      const catName = stripped.trim().slice(2).replace(/:$/, '').trim();
      lastCatIdx = i;
      if (catName.toLowerCase().startsWith('recommended by')) recommendedByIdx = i;
    }
  }

  if (recommender && recommendedByIdx >= 0) {
    const recLower = recommender.toLowerCase().trim();
    let subsectionIdx = -1;
    let subsectionEnd = -1;

    for (let i = recommendedByIdx + 1; i < lines.length; i++) {
      const stripped = lines[i].trimEnd();
      if (!stripped.trim()) continue;
      const ind = indentOf(stripped);
      if (ind <= 4) break;
      if (ind === 8 && stripped.trim().startsWith('- ') && !TODO_RE.test(stripped)) {
        if (subsectionIdx >= 0) { subsectionEnd = i; break; }
        const name = stripped.trim().slice(2).replace(/:$/, '').trim();
        if (name.toLowerCase() === recLower) {
          subsectionIdx = i;
          subsectionEnd = -1;
        }
      }
    }
    if (subsectionIdx >= 0) {
      if (subsectionEnd === -1) {
        subsectionEnd = subsectionIdx + 1;
        while (subsectionEnd < lines.length) {
          const stripped = lines[subsectionEnd].trimEnd();
          if (!stripped.trim()) { subsectionEnd++; continue; }
          const ind = indentOf(stripped);
          if (ind <= 8 && !(TODO_RE.test(stripped) && ind === 8)) {
            if (ind <= 4) break;
            if (ind === 8 && stripped.trim().startsWith('- ') && !TODO_RE.test(stripped)) break;
          }
          subsectionEnd++;
        }
      }
      return { index: subsectionEnd, indent: 12, newLines: null };
    }

    let recEnd = recommendedByIdx + 1;
    while (recEnd < lines.length) {
      const stripped = lines[recEnd].trimEnd();
      if (!stripped.trim()) { recEnd++; continue; }
      if (indentOf(stripped) <= 4) break;
      recEnd++;
    }
    return { index: recEnd, indent: 12, newLines: [`        - ${recommender}\n`] };
  }

  if (recommender && recommendedByIdx === -1 && toWatchStart >= 0) {
    let twEnd = toWatchStart + 1;
    while (twEnd < lines.length) {
      const stripped = lines[twEnd].trimEnd();
      if (!stripped.trim()) { twEnd++; continue; }
      if (indentOf(stripped) === 0) break;
      twEnd++;
    }
    return {
      index: twEnd,
      indent: 12,
      newLines: [`    - Recommended by\n`, `        - ${recommender}\n`],
    };
  }

  if (lastCatIdx >= 0) {
    let insertAt = lastCatIdx + 1;
    while (insertAt < lines.length) {
      const stripped = lines[insertAt].trimEnd();
      if (!stripped.trim()) { insertAt++; continue; }
      if (indentOf(stripped) <= 4) break;
      insertAt++;
    }
    return { index: insertAt, indent: 8, newLines: null };
  }
  return null;
}

// ── Section-end finder (used by route.js) ────────────────────────────────────

// Find the insert point at the end of a top-level section, optionally inside a
// named category. Returns { insertIdx, placeholderIdx } where placeholderIdx
// points at any leading "- " placeholder line that should be consumed on the
// first real insert. Returns null if the section/category is missing.
export function findSectionEnd(lines, sectionName, categoryName = null) {
  const sectionLower = sectionName.toLowerCase();
  const catLower = categoryName ? categoryName.toLowerCase() : null;

  let sectionStart = -1, sectionEnd = -1;
  for (let i = 0; i < lines.length; i++) {
    const s = lines[i].trimEnd();
    if (!s.trim()) continue;
    const ind = indentOf(s);
    if (ind === 0 && s.trim().startsWith('- ')) {
      const name = s.trim().slice(2).replace(/:$/, '').trim();
      if (sectionStart >= 0) { sectionEnd = i; break; }
      if (name.toLowerCase() === sectionLower) sectionStart = i;
    }
  }
  if (sectionStart < 0) return null;
  if (sectionEnd < 0) sectionEnd = lines.length;

  if (!catLower) {
    let placeholder = null;
    for (let i = sectionStart + 1; i < sectionEnd; i++) {
      if (lines[i].trim() === '-') { placeholder = i; break; }
    }
    let insertIdx = sectionEnd;
    while (insertIdx > sectionStart + 1 && !lines[insertIdx - 1].trim()) insertIdx--;
    return { insertIdx, placeholderIdx: placeholder };
  }

  let catStart = -1, catEnd = -1;
  for (let i = sectionStart + 1; i < sectionEnd; i++) {
    const s = lines[i].trimEnd();
    if (!s.trim()) continue;
    const ind = indentOf(s);
    if (ind === 4 && s.trim().startsWith('- ') && !TODO_RE.test(s)) {
      const name = s.trim().slice(2).replace(/:$/, '').trim();
      if (catStart >= 0) { catEnd = i; break; }
      if (name.toLowerCase() === catLower) catStart = i;
    }
  }
  if (catStart < 0) return null;
  if (catEnd < 0) catEnd = sectionEnd;

  let placeholder = null;
  for (let i = catStart + 1; i < catEnd; i++) {
    if (lines[i].trim() === '-') { placeholder = i; break; }
  }
  let insertIdx = catEnd;
  while (insertIdx > catStart + 1 && !lines[insertIdx - 1].trim()) insertIdx--;
  return { insertIdx, placeholderIdx: placeholder };
}
