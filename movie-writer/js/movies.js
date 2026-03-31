// Parse and modify movies.log (ported from movies/movie Python CLI)

const TODO_RE = /^(\s*)\[([x\-? ]?)\]\s*(.+?)\s*$/i;

// Parse movies.log into structured data for display
export function parseMovies(text) {
  const lines = text.split('\n');
  const movies = [];
  let currentSection = null; // 'watched' or 'to watch'
  let currentCategory = null;
  let currentSubsection = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const stripped = line.trimEnd();
    if (!stripped.trim()) continue;

    const indent = stripped.length - stripped.trimStart().length;

    // Root sections (indent 0)
    if (indent === 0 && stripped.trim().startsWith('- ')) {
      const name = stripped.trim().slice(2).replace(/:$/, '').trim();
      if (name.toLowerCase().includes('watch') && !name.toLowerCase().includes('to')) {
        currentSection = 'watched';
      } else if (name.toLowerCase().includes('to watch') || name.toLowerCase() === 'to watch') {
        currentSection = 'to_watch';
      }
      currentCategory = null;
      currentSubsection = null;
      continue;
    }
    // Also handle "- To Watch" without colon
    if (indent === 0 && stripped.trim().toLowerCase().startsWith('- to watch')) {
      currentSection = 'to_watch';
      currentCategory = null;
      currentSubsection = null;
      continue;
    }

    // Categories (indent 4)
    if (indent === 4 && stripped.trim().startsWith('- ')) {
      currentCategory = stripped.trim().slice(2).replace(/:$/, '').trim();
      currentSubsection = null;
      continue;
    }

    // Subsections under "Recommended by" (indent 8, not a todo item)
    if (indent === 8 && stripped.trim().startsWith('- ') && !TODO_RE.test(stripped)) {
      currentSubsection = stripped.trim().slice(2).replace(/:$/, '').trim();
      continue;
    }

    // Movie entries
    const m = TODO_RE.exec(stripped);
    if (m) {
      const movieIndent = m[1].length;
      const status = m[2].trim();
      const title = m[3].trim();
      const props = parseProperties(lines, i, movieIndent);

      movies.push({
        lineIndex: i,
        indent: movieIndent,
        title,
        status, // 'x' = watched, '' = unwatched, '-' = in-progress, '?' = uncertain
        watched: status.toLowerCase() === 'x',
        section: currentSection,
        category: currentCategory,
        subsection: currentSubsection,
        ...props,
      });
    }
  }

  return movies;
}

function parseProperties(lines, movieIdx, movieIndent) {
  const props = {};
  const propIndent = movieIndent + 4;
  let idx = movieIdx + 1;
  let castList = [];
  let inCast = false;
  let reviewLines = [];
  let inReview = false;

  while (idx < lines.length) {
    const line = lines[idx];
    const stripped = line.trimEnd();
    if (!stripped.trim()) { idx++; continue; }

    const lineIndent = stripped.length - stripped.trimStart().length;
    if (lineIndent <= movieIndent) break;

    const content = stripped.trim();

    // Sub-items (cast members, multiline review)
    if (lineIndent >= propIndent + 4 && content.startsWith('- ')) {
      if (inCast) {
        castList.push(content.slice(2).trim());
      } else if (inReview) {
        reviewLines.push(content.slice(2).trim());
      }
      idx++;
      continue;
    }

    inCast = false;
    inReview = false;

    // Property line: "- Key: Value" or "Key: Value"
    let propContent = content;
    if (propContent.startsWith('- ')) propContent = propContent.slice(2);

    const colonIdx = propContent.indexOf(':');
    if (colonIdx > 0) {
      const key = propContent.slice(0, colonIdx).trim().toLowerCase();
      const val = propContent.slice(colonIdx + 1).trim();

      if (key === 'cast' || key === 'cast (imdb)') {
        inCast = true;
        castList = [];
        props.castKey = key;
      } else if (key === 'review') {
        if (val) {
          reviewLines = [val];
        } else {
          inReview = true;
          reviewLines = [];
        }
      } else if (key === 'director' || key === 'director ') {
        // May have both user-set and IMDb director
        if (!props.director) props.director = val;
      } else if (key === 'year') {
        props.year = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'imdb rating') {
        props.rating = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'genres') {
        props.genres = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'country' || key === 'country ') {
        props.country = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'duration') {
        props.duration = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'synopsis') {
        props.synopsis = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'recommender' || key === 'recommmender' || key === 'receommender') {
        props.recommender = val;
      } else if (key === 'imdb') {
        props.imdb = val;
      } else if (key === 'released') {
        props.released = val.replace(/\s*\(IMDb\)\s*$/, '');
      } else if (key === 'tag') {
        props.tag = val;
      } else if (key === 'notes' || key === 'because of') {
        props.notes = (props.notes ? props.notes + '; ' : '') + val;
      }
    }
    idx++;
  }

  if (castList.length > 0) props.cast = castList;
  if (reviewLines.length > 0) props.review = reviewLines.join(' ');

  return props;
}

// Find a movie by title (case-insensitive). Returns { index, indent, match } or null
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

// Find the index after a movie's existing children
export function findInsertAfter(lines, movieIdx, movieIndent) {
  let idx = movieIdx + 1;
  while (idx < lines.length) {
    const stripped = lines[idx].trimEnd();
    if (!stripped.trim()) { idx++; continue; }
    const lineIndent = stripped.length - stripped.trimStart().length;
    if (lineIndent <= movieIndent) break;
    idx++;
  }
  return idx;
}

// Find insertion point in "To Watch" > "Recommended by" > recommender subsection.
// If recommender subsection doesn't exist, creates it.
// If no recommender given, appends to end of last category in "To Watch".
export function findToWatchInsert(lines, recommender) {
  let inToWatch = false;
  let recommendedByIdx = -1;
  let recommendedByEnd = -1;
  let lastCatIdx = -1;
  let toWatchStart = -1;

  for (let i = 0; i < lines.length; i++) {
    const stripped = lines[i].trimEnd();
    if (!stripped.trim()) continue;
    const indent = stripped.length - stripped.trimStart().length;

    // Root section
    if (indent === 0) {
      if (inToWatch) break; // left To Watch
      if (stripped.trim().toLowerCase().replace(/[^a-z ]/g, '').includes('to watch')) {
        inToWatch = true;
        toWatchStart = i;
      }
      continue;
    }

    if (!inToWatch) continue;

    // Category (indent 4)
    if (indent === 4 && stripped.trim().startsWith('- ')) {
      const catName = stripped.trim().slice(2).replace(/:$/, '').trim();
      lastCatIdx = i;
      if (catName.toLowerCase().startsWith('recommended by')) {
        recommendedByIdx = i;
      }
    }
  }

  // If we have a recommender and "Recommended by" exists, find or create their subsection
  if (recommender && recommendedByIdx >= 0) {
    const recLower = recommender.toLowerCase().trim();
    let subsectionIdx = -1;
    let subsectionEnd = -1;

    // Scan inside "Recommended by" for the matching subsection
    for (let i = recommendedByIdx + 1; i < lines.length; i++) {
      const stripped = lines[i].trimEnd();
      if (!stripped.trim()) continue;
      const indent = stripped.length - stripped.trimStart().length;
      if (indent <= 4) break; // left "Recommended by"

      // Subsection header (indent 8, starts with "- ", not a todo item)
      if (indent === 8 && stripped.trim().startsWith('- ') && !TODO_RE.test(stripped)) {
        if (subsectionIdx >= 0) subsectionEnd = i; // end of previous subsection
        const name = stripped.trim().slice(2).replace(/:$/, '').trim();
        if (name.toLowerCase() === recLower) {
          subsectionIdx = i;
          subsectionEnd = -1; // will find the end
        } else if (subsectionIdx >= 0 && subsectionEnd === -1) {
          // We found the next subsection after our match
          subsectionEnd = i;
          break;
        }
      }

      // If we found the subsection, track end
      if (subsectionIdx >= 0 && subsectionEnd === -1) {
        // Still inside our subsection
      }
    }

    // Found existing subsection
    if (subsectionIdx >= 0) {
      // Find end of this subsection
      if (subsectionEnd === -1) {
        subsectionEnd = subsectionIdx + 1;
        while (subsectionEnd < lines.length) {
          const stripped = lines[subsectionEnd].trimEnd();
          if (!stripped.trim()) { subsectionEnd++; continue; }
          const indent = stripped.length - stripped.trimStart().length;
          if (indent <= 8 && !(TODO_RE.test(stripped) && indent === 8)) {
            // Check if it's a movie at indent 8 (part of subsection) or a new subsection/category
            if (indent <= 4) break;
            if (indent === 8 && stripped.trim().startsWith('- ') && !TODO_RE.test(stripped)) break;
          }
          subsectionEnd++;
        }
      }
      return { index: subsectionEnd, indent: 12, newLines: null };
    }

    // Subsection doesn't exist, need to create it
    // Find end of "Recommended by" section
    let recEnd = recommendedByIdx + 1;
    while (recEnd < lines.length) {
      const stripped = lines[recEnd].trimEnd();
      if (!stripped.trim()) { recEnd++; continue; }
      const indent = stripped.length - stripped.trimStart().length;
      if (indent <= 4) break;
      recEnd++;
    }
    // Insert new subsection header at the end of "Recommended by"
    const newSubsection = `        - ${recommender}\n`;
    return { index: recEnd, indent: 12, newLines: [newSubsection] };
  }

  // If we have a recommender but no "Recommended by" section exists, create it
  if (recommender && recommendedByIdx === -1 && toWatchStart >= 0) {
    // Find end of "To Watch" section
    let twEnd = toWatchStart + 1;
    while (twEnd < lines.length) {
      const stripped = lines[twEnd].trimEnd();
      if (!stripped.trim()) { twEnd++; continue; }
      const indent = stripped.length - stripped.trimStart().length;
      if (indent === 0) break;
      twEnd++;
    }
    const newLines = [
      `    - Recommended by\n`,
      `        - ${recommender}\n`,
    ];
    return { index: twEnd, indent: 12, newLines };
  }

  // No recommender: append to end of last category in "To Watch"
  if (lastCatIdx >= 0) {
    let insertAt = lastCatIdx + 1;
    while (insertAt < lines.length) {
      const stripped = lines[insertAt].trimEnd();
      if (!stripped.trim()) { insertAt++; continue; }
      const indent = stripped.length - stripped.trimStart().length;
      if (indent <= 4) break;
      insertAt++;
    }
    return { index: insertAt, indent: 8, newLines: null };
  }

  return null;
}

// Build a new movie entry as lines
export function buildMovieEntry(title, { recommender, director, year, review } = {}, indent = 12) {
  const pad = ' '.repeat(indent);
  const propPad = ' '.repeat(indent + 4);
  const entryLines = [`${pad}[] ${title}\n`];

  if (recommender) entryLines.push(`${propPad}- Recommender: ${recommender}\n`);
  if (director) entryLines.push(`${propPad}- Director: ${director}\n`);
  if (year) entryLines.push(`${propPad}- Year: ${year}\n`);
  if (review) entryLines.push(`${propPad}- review: ${review}\n`);

  return entryLines;
}

// Mark a movie as watched: replace checkbox content with [x]
export function markWatched(lines, movieIdx) {
  lines[movieIdx] = lines[movieIdx].replace(/\[[x\-? ]?\]/i, '[x]');
  return lines;
}

// Mark a movie as unwatched: replace checkbox content with []
export function markUnwatched(lines, movieIdx) {
  lines[movieIdx] = lines[movieIdx].replace(/\[[x\-? ]?\]/i, '[]');
  return lines;
}

// Add or update a review on a movie
export function setReview(lines, movieIdx, movieIndent, text) {
  const propPad = ' '.repeat(movieIndent + 4);
  const insertAt = findInsertAfter(lines, movieIdx, movieIndent);

  // Check if review already exists
  for (let i = movieIdx + 1; i < insertAt; i++) {
    const stripped = lines[i].trim();
    if (stripped.startsWith('- review:') || stripped.startsWith('review:')) {
      // Replace existing review line
      lines[i] = `${propPad}- review: ${text}\n`;
      // Remove any multiline continuation of old review
      let j = i + 1;
      while (j < lines.length) {
        const s = lines[j].trimEnd();
        if (!s.trim()) { j++; continue; }
        const ind = s.length - s.trimStart().length;
        if (ind >= movieIndent + 8 && s.trim().startsWith('- ')) {
          // Could be review continuation
          lines.splice(j, 1);
        } else {
          break;
        }
      }
      return lines;
    }
  }

  // No existing review, insert new one
  lines.splice(insertAt, 0, `${propPad}- review: ${text}\n`);
  return lines;
}

// Update or add a property on a movie
export function setProperty(lines, movieIdx, movieIndent, key, value) {
  const propPad = ' '.repeat(movieIndent + 4);
  const insertAt = findInsertAfter(lines, movieIdx, movieIndent);
  const keyLower = key.toLowerCase();

  // Check if property exists
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

  // Property doesn't exist, insert
  lines.splice(insertAt, 0, `${propPad}- ${key}: ${value}\n`);
  return lines;
}
