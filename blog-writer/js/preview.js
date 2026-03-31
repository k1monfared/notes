// Markdown preview using marked.js

let markedLoaded = false;

async function ensureMarked() {
  if (markedLoaded) return;
  // marked is loaded via script tag in index.html
  if (typeof marked === 'undefined') {
    throw new Error('marked.js not loaded');
  }
  marked.setOptions({
    breaks: true,
    gfm: true,
  });
  markedLoaded = true;
}

export async function renderPreview(markdown, imageBlobs = {}) {
  await ensureMarked();
  let html = marked.parse(markdown);

  // Replace image references with blob URLs for local preview
  for (const [ref, blobUrl] of Object.entries(imageBlobs)) {
    html = html.replace(
      new RegExp(`src="${escapeRegex(ref)}"`, 'g'),
      `src="${blobUrl}"`
    );
  }

  return html;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
