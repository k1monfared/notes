// Filename generation following YYYYMMDD_slug.md convention

export function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}${m}${d}`;
}

export function displayDate(dateStr) {
  // Convert YYYYMMDD to readable format
  const y = parseInt(dateStr.slice(0, 4));
  const m = parseInt(dateStr.slice(4, 6)) - 1;
  const d = parseInt(dateStr.slice(6, 8));
  return new Date(y, m, d).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function titleToSlug(title) {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s\u0600-\u06FF\u0750-\u077F]/g, '') // keep alphanumeric, spaces, Unicode (Persian etc)
    .replace(/\s+/g, '_')                                // spaces to underscores
    .replace(/_+/g, '_')                                 // collapse multiple underscores
    .replace(/^_|_$/g, '');                               // trim underscores
}

export function generateFilename(date, title, isDraft = false) {
  const dateStr = formatDate(date);
  const slug = titleToSlug(title);
  const ext = isDraft ? 'draft' : 'md';
  return `${dateStr}_${slug}.${ext}`;
}

export function parseFilename(filename) {
  const stem = filename.replace(/\.(md|draft)$/, '');
  const match = stem.match(/^(\d{8})_(.+)$/);
  if (!match) return null;
  return {
    dateStr: match[1],
    slug: match[2],
    urlSlug: `${match[1]}-${match[2].replace(/_/g, '-')}`,
    isDraft: filename.endsWith('.draft'),
  };
}

export function imageDir(dateStr) {
  return `files/${dateStr}`;
}
