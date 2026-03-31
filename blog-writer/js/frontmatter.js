// Parse and generate YAML frontmatter (matching build.py conventions)

export function parse(text) {
  const meta = {};
  if (!text.startsWith('---')) return { meta, body: text };
  const parts = text.split('---', 3);
  if (parts.length < 3) return { meta, body: text };
  for (const line of parts[1].trim().split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim().toLowerCase();
    const val = line.slice(idx + 1).trim();
    meta[key] = val;
  }
  return { meta, body: parts[2] };
}

export function generate(meta) {
  const lines = [];
  for (const [key, val] of Object.entries(meta)) {
    if (val) lines.push(`${key}: ${val}`);
  }
  if (lines.length === 0) return '';
  return `---\n${lines.join('\n')}\n---\n`;
}

export function buildPostContent(title, tags, body) {
  const meta = {};
  if (tags.trim()) meta.tags = tags.trim();
  const frontmatter = generate(meta);
  const heading = `# ${title.trim()}\n\n`;
  return frontmatter + heading + body.trim() + '\n';
}

export function extractFromContent(content) {
  const { meta, body } = parse(content);
  const tags = meta.tags || '';

  // Extract title from first heading
  let title = '';
  let bodyWithoutTitle = body;
  const lines = body.trim().split('\n');
  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].trim().match(/^#{1,6}\s+(.+?)(?:\s*#*\s*)?$/);
    if (match) {
      title = match[1].replace(/\*\*(.+?)\*\*/g, '$1').trim();
      bodyWithoutTitle = [...lines.slice(0, i), ...lines.slice(i + 1)].join('\n').trim();
      break;
    }
    // Setext heading
    if (i + 1 < lines.length && lines[i].trim() && /^[=-]+$/.test(lines[i + 1].trim())) {
      title = lines[i].trim().replace(/\*\*(.+?)\*\*/g, '$1');
      bodyWithoutTitle = [...lines.slice(0, i), ...lines.slice(i + 2)].join('\n').trim();
      break;
    }
  }

  return { title, tags, body: bodyWithoutTitle };
}
