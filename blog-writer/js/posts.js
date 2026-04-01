// Post management: list, create, edit, publish

import { listFiles, getFile, createCommit, renameFile } from './github.js';
import { parseFilename, displayDate, generateFilename, formatDate, imageDir } from './naming.js';
import { buildPostContent, extractFromContent } from './frontmatter.js';
import { getStoredImages } from './images.js';
import { setCache, getCache } from './storage.js';

export async function fetchPostList(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = await getCache('postList');
    if (cached) return cached;
  }

  const files = await listFiles('blog');
  const posts = files
    .filter(f => f.type === 'file' && /^\d{8}_/.test(f.name) && /\.(md|draft)$/.test(f.name))
    .map(f => {
      const parsed = parseFilename(f.name);
      if (!parsed) return null;
      return {
        filename: f.name,
        path: f.path,
        sha: f.sha,
        dateStr: parsed.dateStr,
        date: displayDate(parsed.dateStr),
        slug: parsed.slug,
        isDraft: parsed.isDraft,
        title: parsed.slug.replace(/_/g, ' '),
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.dateStr.localeCompare(a.dateStr));

  await setCache('postList', posts);
  return posts;
}

export async function loadPost(path) {
  const file = await getFile(path);
  const { title, tags, body } = extractFromContent(file.content);
  return { title, tags, body, rawContent: file.content, sha: file.sha, path: file.path };
}

export async function publishPost({ title, tags, body, date, images, isDraft = false }) {
  const dateStr = formatDate(date);
  const filename = generateFilename(date, title, isDraft);
  const content = buildPostContent(title, tags, body);

  const files = [
    { path: `blog/${filename}`, content, encoding: 'utf-8' },
  ];

  // Add images
  if (images && images.length > 0) {
    for (const img of images) {
      files.push({
        path: `blog/${imageDir(dateStr)}/${img.name}`,
        content: img.base64,
        encoding: 'base64',
      });
    }
  }

  const action = isDraft ? 'Save draft' : 'Add blog post';
  const message = `${action}: ${title}`;
  return createCommit(files, message);
}

export async function updatePost({ originalPath, title, tags, body, date, newImages, isDraft = false }) {
  const dateStr = formatDate(date);
  const filename = generateFilename(date, title, isDraft);
  const content = buildPostContent(title, tags, body);
  const newPath = `blog/${filename}`;

  const imageFiles = [];
  if (newImages && newImages.length > 0) {
    for (const img of newImages) {
      imageFiles.push({
        path: `blog/${imageDir(dateStr)}/${img.name}`,
        content: img.base64,
        encoding: 'base64',
      });
    }
  }

  const action = isDraft ? 'Save draft' : 'Update blog post';
  const message = `${action}: ${title}`;

  if (originalPath !== newPath) {
    // Path changed (different date, slug, or draft status). Delete old file atomically.
    return renameFile(originalPath, newPath, content, message, imageFiles);
  }

  // Same path, just update in place
  const files = [{ path: newPath, content, encoding: 'utf-8' }, ...imageFiles];
  return createCommit(files, message);
}

export async function publishDraft(draftPath, title, tags, body, date) {
  const content = buildPostContent(title, tags, body);
  const filename = generateFilename(date, title, false);
  const newPath = `blog/${filename}`;
  return renameFile(draftPath, newPath, content, `Publish draft: ${title}`);
}

export async function unpublishPost(publishedPath, title, tags, body, date) {
  const content = buildPostContent(title, tags, body);
  const filename = generateFilename(date, title, true);
  const newPath = `blog/${filename}`;
  return renameFile(publishedPath, newPath, content, `Unpublish: ${title}`);
}
