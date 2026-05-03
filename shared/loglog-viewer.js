/**
 * Generic loglog viewer — parses hierarchical plain-text .log files
 * and renders an interactive collapsible tree UI.
 *
 * Usage:
 *   createLoglogViewer(document.getElementById('app'), {
 *     title: 'Books',
 *     dataFile: '../books.log',
 *     checkboxes: true,
 *     tiers: ['I highly recommend', 'I recommend', ...],
 *     summaryField: 'author',
 *     propertyRenderers: { goodreads: (v) => `<a href="${v}" ...>Goodreads</a>` }
 *   });
 */

/* ── Phase 1: Build indent tree ── */

function buildTree(text) {
  const lines = text.split('\n');
  const root = { raw: '', indent: -1, children: [], lineIdx: -1 };
  const stack = [root];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    if (raw.trim() === '') continue;
    const indent = raw.search(/\S/);
    const content = raw.trim();

    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const node = { raw: content, indent, children: [], lineIdx: i };
    stack[stack.length - 1].children.push(node);
    stack.push(node);
  }

  return root.children;
}

/* ── Phase 2: Classify nodes ── */

// Does a raw line look like a property (key: value or key:)?
function isPropertyLine(raw) {
  return /^-?\s*\w[\w\s/&'()\-]*?:\s/.test(raw) || /^-?\s*\w[\w\s/&'()\-]*?:\s*$/.test(raw);
}

// Can this tree node be treated as a property/text of its parent item?
// Only used to determine if parent is item vs section.
function canBeProperty(node) {
  // Property with value or key-only with colon
  if (isPropertyLine(node.raw)) return true;
  // Simple text leaf (no children, no checkbox)
  if (node.children.length === 0 && !node.raw.match(/^\[/)) return true;
  return false;
}

function classifyTree(rawNodes, config) {
  const tierSet = new Set((config.tiers || []).map(t => t.toLowerCase()));
  const result = [];
  for (const node of rawNodes) {
    const c = classifyNode(node, tierSet, config, 0);
    if (c) result.push(c);
  }
  return result;
}

function classifyNode(node, tierSet, config, depth) {
  const raw = node.raw;

  // Detect checkbox: [x], [ ], [], [-], [?]
  const cbMatch = raw.match(/^\[([x \-?]?)\]\s*(.*)/i);

  const name = cbMatch
    ? cbMatch[2].replace(/:$/, '').trim()
    : raw.replace(/^-\s*/, '').replace(/:$/, '').trim();

  // Skip empty nodes (bare dashes, empty checkboxes)
  if (!name && node.children.length === 0) return null;

  const isTier = tierSet.has(name.toLowerCase());
  const isBareName = !cbMatch && !raw.startsWith('- ') && raw !== '-';

  // ── Checkbox items → always items ──
  if (cbMatch) {
    if (!name && node.children.length === 0) return null;
    const item = { type: 'item', name, depth, lineIdx: node.lineIdx, indent: node.indent, checkbox: (cbMatch[1] || ' ').toLowerCase(), properties: {}, childTexts: [] };
    if (node.children.length > 0) extractProperties(node.children, item);
    return item;
  }

  // ── Tier names → always sections ──
  if (isTier) {
    const children = classifyChildren(node.children, tierSet, config, depth + 1);
    return { type: 'section', name, depth, lineIdx: node.lineIdx, indent: node.indent, isTier: true, children };
  }

  // ── Bare name with children → section or item ──
  if (isBareName && node.children.length > 0) {
    // If all children are property-like → item (e.g., a place with descriptions/URLs)
    const allProp = node.children.every(c => canBeProperty(c));
    if (allProp) {
      const item = { type: 'item', name, depth, lineIdx: node.lineIdx, indent: node.indent, properties: {}, childTexts: [] };
      extractProperties(node.children, item);
      return item;
    }
    const children = classifyChildren(node.children, tierSet, config, depth + 1);
    return { type: 'section', name, depth, lineIdx: node.lineIdx, indent: node.indent, children };
  }

  // ── No children → leaf item ──
  if (node.children.length === 0) {
    return { type: 'item', name, depth, lineIdx: node.lineIdx, indent: node.indent, properties: {}, childTexts: [] };
  }

  // ── Dash-prefixed with children: decide section vs item ──

  // If all children are simple text leaves with no properties → section (sub-categories)
  const allSimpleTextLeaves = node.children.every(c =>
    c.children.length === 0 && !isPropertyLine(c.raw)
  );
  if (allSimpleTextLeaves && node.children.length >= 2) {
    const children = classifyChildren(node.children, tierSet, config, depth + 1);
    return { type: 'section', name, depth, lineIdx: node.lineIdx, indent: node.indent, children };
  }

  // If all children can be properties/text → item
  const allProp = node.children.every(c => canBeProperty(c));
  if (allProp) {
    const item = { type: 'item', name, depth, lineIdx: node.lineIdx, indent: node.indent, properties: {}, childTexts: [] };
    extractProperties(node.children, item);
    return item;
  }

  // Has non-property children → section
  const children = classifyChildren(node.children, tierSet, config, depth + 1);
  return { type: 'section', name, depth, lineIdx: node.lineIdx, indent: node.indent, children };
}

function classifyChildren(rawChildren, tierSet, config, depth) {
  const result = [];
  for (const c of rawChildren) {
    const classified = classifyNode(c, tierSet, config, depth);
    if (classified) result.push(classified);
  }
  return result;
}

/* ── Property extraction (for items) ── */

function extractProperties(children, item) {
  for (const child of children) {
    const raw = child.raw;

    // Property with value: "- key: value" or "key: value"
    const propValMatch = raw.match(/^-?\s*(\w[\w\s/&'()\-]*?):\s+(.+)$/);
    if (propValMatch) {
      const key = propValMatch[1].trim().toLowerCase();
      let val = propValMatch[2].trim();
      if (child.children.length > 0) {
        val += '\n' + collectText(child.children);
      }
      item.properties[key] = val;
      continue;
    }

    // Property key only with colon: "- key:" or "key:"
    const propKeyMatch = raw.match(/^-?\s*(\w[\w\s/&'()\-]*?):\s*$/);
    if (propKeyMatch) {
      const key = propKeyMatch[1].trim().toLowerCase();
      if (child.children.length > 0) {
        // Check if children are all key:value pairs → merge individually
        const allKV = child.children.every(c => /^-?\s*\w[\w\s/&'()\-]*?:\s+.+$/.test(c.raw));
        if (allKV) {
          for (const c of child.children) {
            const m = c.raw.match(/^-?\s*(\w[\w\s/&'()\-]*?):\s+(.+)$/);
            if (m) {
              let v = m[2].trim();
              if (c.children.length > 0) v += '\n' + collectText(c.children);
              item.properties[m[1].trim().toLowerCase()] = v;
            }
          }
        } else {
          item.properties[key] = collectText(child.children);
        }
      } else {
        item.properties[key] = '';
      }
      continue;
    }

    // Bare name with children (no colon): "- Author", "- review"
    if (child.children.length > 0) {
      const bareName = raw.replace(/^-\s*/, '').replace(/:$/, '').trim().toLowerCase();
      item.properties[bareName] = collectText(child.children);
      continue;
    }

    // Plain text child
    const text = raw.replace(/^-\s*/, '').trim();
    if (text) item.childTexts.push(text);
  }
}

function collectText(children) {
  const parts = [];
  for (const c of children) {
    const text = c.raw.replace(/^-\s*/, '').trim();
    if (text) parts.push(text);
    if (c.children.length > 0) {
      const sub = collectText(c.children);
      if (sub) parts.push(sub);
    }
  }
  return parts.join('\n');
}

/* ── Renderer ── */

function linkify(text) {
  if (!text) return '';
  return text.replace(/(https?:\/\/[^\s<>"']+)/g, '<a href="$1" target="_blank" rel="noopener" class="ext-link">$1</a>');
}

function escHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function createLoglogViewer(container, config) {
  const {
    title = 'Viewer',
    dataFile,
    checkboxes = false,
    tiers = null,
  } = config;

  container.innerHTML = `
    <div id="hdr">
      <div class="title-row">
        <h1>${escHtml(title)}</h1>
        <div class="hdr-actions"></div>
      </div>
      <div class="search-row">
        <input id="search" type="text" placeholder="Search… (use key:value for field search)" autocomplete="off">
        <span id="search-count"></span>
      </div>
    </div>
    <div id="stats"></div>
    <div id="content"><div class="center">Loading…</div></div>`;

  const searchEl = container.querySelector('#search');
  const countEl = container.querySelector('#search-count');
  const statsEl = container.querySelector('#stats');
  const contentEl = container.querySelector('#content');

  // Render once we have text (either from initial fetch or after a save).
  function renderFromText(text) {
    const tree = buildTree(text);
    const nodes = classifyTree(tree, config);

    if (tiers) {
      const tierLower = tiers.map(t => t.toLowerCase());
      for (const n of nodes) {
        const idx = tierLower.indexOf((n.name || '').toLowerCase());
        if (idx !== -1) n.tierIndex = idx + 1;
      }
    }

    let totalItems = 0, checkedItems = 0;
    function countItems(ns) {
      for (const n of ns) {
        if (n.type === 'item') { totalItems++; if (n.checkbox === 'x') checkedItems++; }
        if (n.children) countItems(n.children);
      }
    }
    countItems(nodes);
    statsEl.textContent = checkboxes
      ? `${checkedItems} / ${totalItems} done`
      : `${totalItems} items`;

    contentEl.innerHTML = '';
    renderNodes(contentEl, nodes, config);

    const allItemNodes = [];
    collectAllItemNodes(nodes, allItemNodes);

    // Stash state so the editor (loaded as a sibling script) can find raw
    // text + parsed item nodes for in-place save + refresh.
    container.__loglogState = {
      text, nodes, items: allItemNodes, dataFile, config,
      refresh: (newText) => renderFromText(newText),
    };

    // Notify any listeners (the editor) that fresh state is available.
    container.dispatchEvent(new CustomEvent('loglog-rendered', { detail: container.__loglogState }));

    return allItemNodes;
  }

  fetch(dataFile)
    .then(r => { if (!r.ok) throw new Error(r.status); return r.text(); })
    .then(text => {
      const allItemNodes = renderFromText(text);
      searchEl.addEventListener('input', () => {
        const q = searchEl.value.trim();
        filterNodes(contentEl, q, countEl, container.__loglogState.items);
      });
    })
    .catch(err => {
      contentEl.innerHTML = `<div class="center err">Failed to load: ${escHtml(String(err))}</div>`;
    });
}

function collectAllItemNodes(nodes, out) {
  for (const n of nodes) {
    if (n.type === 'item') out.push(n);
    if (n.children) collectAllItemNodes(n.children, out);
  }
}

function renderNodes(container, nodes, config) {
  for (const node of nodes) {
    if (node.type === 'section') {
      renderSection(container, node, config);
    } else {
      renderItem(container, node, config);
    }
  }
}

function renderSection(container, node, config) {
  const sec = document.createElement('div');
  sec.className = 'sec';
  sec.dataset.depth = node.depth || 0;
  if (node.tierIndex) sec.dataset.tier = node.tierIndex;

  const childItemCount = countDescendantItems(node);
  const checkedCount = config.checkboxes ? countDescendantChecked(node) : 0;
  const metaText = config.checkboxes
    ? `${checkedCount}/${childItemCount}`
    : (childItemCount > 0 ? `${childItemCount}` : '');

  sec.innerHTML = `
    <div class="sec-hdr">
      <span class="sec-title">${escHtml(node.name)}</span>
      <span class="sec-meta"><span>${metaText}</span> <span class="arr">▶</span></span>
    </div>
    <div class="sec-body"></div>`;

  sec.querySelector('.sec-hdr').addEventListener('click', () => sec.classList.toggle('open'));

  const body = sec.querySelector('.sec-body');
  if (node.children && node.children.length > 0) {
    renderNodes(body, node.children, config);
  }

  // Auto-open top-level sections
  if ((node.depth || 0) === 0) sec.classList.add('open');

  container.appendChild(sec);
}

function renderItem(container, node, config) {
  const { checkboxes = false, summaryField, reviewFields = ['review'], linkFields = ['link', 'goodreads', 'website'] } = config;
  const item = document.createElement('div');
  item.className = 'item';
  item.dataset.depth = node.depth || 0;
  item.dataset.name = (node.name || '').toLowerCase();
  // Editor uses these to locate the item in the raw text.
  if (node.lineIdx !== undefined) item.dataset.lineIdx = node.lineIdx;
  if (node.indent !== undefined) item.dataset.indent = node.indent;
  if (node.checkbox !== undefined) item.dataset.checkbox = node.checkbox;

  const props = node.properties || {};
  const hasDetail = Object.keys(props).length > 0 || (node.childTexts && node.childTexts.length > 0);

  // Status icon
  let siHtml = '';
  if (checkboxes && node.checkbox !== undefined) {
    const cls = node.checkbox === 'x' ? 'checked' : node.checkbox === '-' ? 'in-progress' : node.checkbox === '?' ? 'uncertain' : 'unchecked';
    const icon = node.checkbox === 'x' ? '●' : node.checkbox === '-' ? '◐' : node.checkbox === '?' ? '?' : '○';
    siHtml = `<span class="si ${cls}">${icon}</span>`;
  }

  // Summary line
  let summary = '';
  if (summaryField && props[summaryField]) {
    summary = props[summaryField].split('\n')[0];
  } else if (node.childTexts && node.childTexts.length > 0) {
    summary = node.childTexts[0];
  }
  const summaryHtml = summary ? `<div class="item-sub">${escHtml(summary)}</div>` : '';
  const toggleHtml = hasDetail ? '<span class="item-toggle"></span>' : '';

  item.innerHTML = `
    <div class="item-hdr">
      ${siHtml}
      <div class="item-info">
        <div class="item-name">${escHtml(node.name)}</div>
        ${summaryHtml}
      </div>
      ${toggleHtml}
    </div>`;

  if (hasDetail) {
    const detail = document.createElement('div');
    detail.className = 'item-detail';
    renderItemDetail(detail, node, config);
    item.appendChild(detail);
    item.querySelector('.item-hdr').addEventListener('click', () => item.classList.toggle('open'));
  }

  container.appendChild(item);
}

function renderItemDetail(detail, node, config) {
  const props = node.properties || {};
  const { propertyRenderers = {}, reviewFields = ['review'], linkFields = ['link', 'goodreads', 'website'], hideProperties = [] } = config;
  const hideSet = new Set([...(hideProperties || []), config.summaryField].filter(Boolean).map(s => s.toLowerCase()));

  // Reviews first
  for (const rf of reviewFields) {
    if (props[rf]) {
      const div = document.createElement('div');
      div.className = 'review';
      const escaped = escHtml(props[rf]).replace(/\n/g, '<br>');
      div.innerHTML = `<div class="review-label">${escHtml(rf)}</div><div class="review-text">${linkify(escaped)}</div>`;
      detail.appendChild(div);
    }
  }

  // Properties grid
  const gridKeys = Object.keys(props).filter(k => !reviewFields.includes(k) && !hideSet.has(k));
  if (gridKeys.length > 0) {
    const grid = document.createElement('div');
    grid.className = 'dg';
    for (const k of gridKeys) {
      const val = props[k];
      let rendered;
      if (propertyRenderers[k]) {
        rendered = propertyRenderers[k](val);
      } else if (linkFields.includes(k) || /^https?:\/\//.test(val)) {
        const url = val.split('\n')[0].trim();
        rendered = `<a href="${escHtml(url)}" target="_blank" rel="noopener">${escHtml(url)}</a>`;
      } else {
        rendered = linkify(escHtml(val).replace(/\n/g, '<br>'));
      }
      grid.innerHTML += `<span class="dk">${escHtml(k)}</span><span class="dv">${rendered}</span>`;
    }
    detail.appendChild(grid);
  }

  // Child texts
  if (node.childTexts && node.childTexts.length > 0) {
    const list = document.createElement('div');
    list.className = 'children-list';
    for (const t of node.childTexts) {
      const line = document.createElement('div');
      line.className = 'child-line';
      line.innerHTML = linkify(escHtml(t));
      list.appendChild(line);
    }
    detail.appendChild(list);
  }
}

/* ── Advanced Search ── */

function parseSearchQuery(query) {
  // Parse "key:value key2:value2 freetext" into structured query
  const filters = [];
  let freeText = '';
  // Match field:value patterns (value can be quoted or unquoted)
  const fieldRe = /(\w+):"([^"]+)"|(\w+):(\S+)/g;
  let lastEnd = 0;
  let match;

  while ((match = fieldRe.exec(query)) !== null) {
    // Collect any free text before this match
    const before = query.slice(lastEnd, match.index).trim();
    if (before) freeText += (freeText ? ' ' : '') + before;
    lastEnd = match.index + match[0].length;

    const field = (match[1] || match[3]).toLowerCase();
    const value = (match[2] || match[4]).toLowerCase();
    filters.push({ field, value });
  }

  // Remaining text after last match
  const remaining = query.slice(lastEnd).trim();
  if (remaining) freeText += (freeText ? ' ' : '') + remaining;

  return { filters, freeText: freeText.toLowerCase() };
}

function itemMatchesQuery(node, parsed) {
  const props = node.properties || {};

  // Check field filters
  for (const { field, value } of parsed.filters) {
    let fieldContent = '';
    if (field === 'title' || field === 'name') {
      fieldContent = (node.name || '').toLowerCase();
    } else if (props[field]) {
      fieldContent = props[field].toLowerCase();
    } else {
      // Field not found on this item → no match
      return false;
    }
    if (!fieldContent.includes(value)) return false;
  }

  // Check free text against everything
  if (parsed.freeText) {
    const allText = [
      node.name || '',
      ...Object.values(props),
      ...(node.childTexts || [])
    ].join(' ').toLowerCase();
    if (!allText.includes(parsed.freeText)) return false;
  }

  return true;
}

function filterNodes(container, query, countEl, allItemNodes) {
  const items = container.querySelectorAll('.item');
  const sections = container.querySelectorAll('.sec');
  let visible = 0;

  if (!query) {
    items.forEach(el => { el.style.display = ''; el.classList.remove('open'); });
    sections.forEach(el => { el.style.display = ''; });
    countEl.textContent = '';
    return;
  }

  const parsed = parseSearchQuery(query);
  const isAdvanced = parsed.filters.length > 0;

  // Mark items
  let itemIdx = 0;
  items.forEach(el => {
    let matches;
    if (isAdvanced) {
      // Find the matching node for this DOM element
      const name = el.dataset.name || '';
      // Match by walking allItemNodes in order (DOM order = tree order)
      const node = allItemNodes[itemIdx++];
      matches = node ? itemMatchesQuery(node, parsed) : false;
    } else {
      matches = el.textContent.toLowerCase().includes(parsed.freeText);
    }

    if (matches) {
      el.style.display = '';
      el.classList.add('open');
      visible++;
    } else {
      el.style.display = 'none';
      el.classList.remove('open');
    }
  });

  // Show/hide sections (deepest first)
  const secArr = Array.from(sections).reverse();
  for (const sec of secArr) {
    const hasVisible = sec.querySelector('.item:not([style*="display: none"])') ||
                       sec.querySelector('.sec:not([style*="display: none"])');
    if (hasVisible) {
      sec.style.display = '';
      sec.classList.add('open');
    } else {
      const title = sec.querySelector('.sec-title');
      if (parsed.freeText && title && title.textContent.toLowerCase().includes(parsed.freeText)) {
        sec.style.display = '';
        sec.classList.add('open');
        sec.querySelectorAll('.item').forEach(i => { i.style.display = ''; visible++; });
        sec.querySelectorAll('.sec').forEach(s => s.style.display = '');
      } else {
        sec.style.display = 'none';
      }
    }
  }

  countEl.textContent = `${visible} match${visible !== 1 ? 'es' : ''}`;
}

/* ── Helpers ── */

function countDescendantItems(node) {
  let c = 0;
  for (const child of (node.children || [])) {
    if (child.type === 'item') c++;
    c += countDescendantItems(child);
  }
  return c;
}

function countDescendantChecked(node) {
  let c = 0;
  for (const child of (node.children || [])) {
    if (child.type === 'item' && child.checkbox === 'x') c++;
    c += countDescendantChecked(child);
  }
  return c;
}
