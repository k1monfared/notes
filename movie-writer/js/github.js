// GitHub API client (Contents API + Git Trees API)

import { getToken, getRepo } from './auth.js';

const API = 'https://api.github.com';

function headers() {
  return {
    'Authorization': `Bearer ${getToken()}`,
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json',
  };
}

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, { headers: headers(), ...options });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(`GitHub API ${res.status}: ${body.message || res.statusText}`);
  }
  return res.json();
}

// Get a single file's content (decodes base64, handles UTF-8)
export async function getFile(path) {
  const repo = getRepo();
  const data = await request(`/repos/${repo}/contents/${path}`);
  const content = atob(data.content.replace(/\n/g, ''));
  const bytes = Uint8Array.from(content, c => c.charCodeAt(0));
  const text = new TextDecoder().decode(bytes);
  return { content: text, sha: data.sha, path: data.path };
}

// Create a single commit with one or more files (atomic)
export async function createCommit(files, message) {
  const repo = getRepo();

  const ref = await request(`/repos/${repo}/git/refs/heads/main`);
  const baseSha = ref.object.sha;

  const baseCommit = await request(`/repos/${repo}/git/commits/${baseSha}`);
  const baseTreeSha = baseCommit.tree.sha;

  const treeItems = [];
  for (const file of files) {
    const blobData = await request(`/repos/${repo}/git/blobs`, {
      method: 'POST',
      body: JSON.stringify({ content: file.content, encoding: file.encoding || 'utf-8' }),
    });
    treeItems.push({
      path: file.path,
      mode: '100644',
      type: 'blob',
      sha: blobData.sha,
    });
  }

  const tree = await request(`/repos/${repo}/git/trees`, {
    method: 'POST',
    body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems }),
  });

  const commit = await request(`/repos/${repo}/git/commits`, {
    method: 'POST',
    body: JSON.stringify({ message, tree: tree.sha, parents: [baseSha] }),
  });

  await request(`/repos/${repo}/git/refs/heads/main`, {
    method: 'PATCH',
    body: JSON.stringify({ sha: commit.sha }),
  });

  return commit;
}
