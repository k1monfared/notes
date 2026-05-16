// Markdown preview using marked.js

const AUDIO_EXTS = new Set(['mp3', 'm4a', 'wav', 'oga', 'ogg', 'flac', 'opus', 'aac']);
const VIDEO_EXTS = new Set(['mp4', 'mov', 'webm', 'm4v', 'ogv']);
const MEDIA_LINE_RE = /^[ \t]*!\[([^\]]*)\]\(<?([^)>\s]+\.[A-Za-z0-9]+)>?\)[ \t]*$/gm;

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

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function convertMediaLinks(text) {
  return text.replace(MEDIA_LINE_RE, (full, caption, src) => {
    const ext = src.includes('.') ? src.split('.').pop().toLowerCase() : '';
    let kind, media;
    if (AUDIO_EXTS.has(ext)) {
      kind = 'audio';
      media = `<audio controls preload="metadata" src="${escapeHtml(src)}"></audio>`;
    } else if (VIDEO_EXTS.has(ext)) {
      kind = 'video';
      media = `<video controls preload="metadata" playsinline><source src="${escapeHtml(src)}"></video>`;
    } else {
      return full;
    }
    const cap = caption.trim()
      ? `<figcaption>${escapeHtml(caption.trim())}</figcaption>`
      : '';
    return `\n<figure class="${kind}-figure">${media}${cap}</figure>\n`;
  });
}

export async function renderPreview(markdown, imageBlobs = {}) {
  await ensureMarked();
  const processed = convertMediaLinks(markdown);
  let html = marked.parse(processed);

  // Replace media references with blob URLs for local preview (covers <img>, <audio>, <source>)
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
