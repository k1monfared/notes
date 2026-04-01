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

// List files in a directory
export async function listFiles(path) {
  const repo = getRepo();
  return request(`/repos/${repo}/contents/${path}`);
}

// Get a single file's content (decodes base64)
export async function getFile(path) {
  const repo = getRepo();
  const data = await request(`/repos/${repo}/contents/${path}`);
  const content = atob(data.content.replace(/\n/g, ''));
  // Handle UTF-8 properly
  const bytes = Uint8Array.from(content, c => c.charCodeAt(0));
  const text = new TextDecoder().decode(bytes);
  return { content: text, sha: data.sha, path: data.path };
}

// Get file SHA (for updates)
export async function getFileSha(path) {
  try {
    const repo = getRepo();
    const data = await request(`/repos/${repo}/contents/${path}`);
    return data.sha;
  } catch {
    return null;
  }
}

// Create a single commit with multiple files (atomic)
// Retries up to 3 times if the ref moves between fetch and update (e.g. enrichment workflow pushes)
// files: [{ path: 'blog/file.md', content: 'text or base64', encoding: 'utf-8' | 'base64' }]
export async function createCommit(files, message) {
  const repo = getRepo();
  const refPath = `/repos/${repo}/git/refs/heads/main`;

  for (let attempt = 0; attempt < 3; attempt++) {
    const ref = await request(refPath);
    const baseSha = ref.object.sha;

    const baseCommit = await request(`/repos/${repo}/git/commits/${baseSha}`);
    const baseTreeSha = baseCommit.tree.sha;

    const treeItems = [];
    for (const file of files) {
      const blobData = await request(`/repos/${repo}/git/blobs`, {
        method: 'POST',
        body: JSON.stringify({
          content: file.content,
          encoding: file.encoding === 'base64' ? 'base64' : 'utf-8',
        }),
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

    try {
      await request(refPath, {
        method: 'PATCH',
        body: JSON.stringify({ sha: commit.sha }),
      });
      return commit;
    } catch (err) {
      if (err.message.includes('422') && attempt < 2) {
        continue;
      }
      throw err;
    }
  }
}

// Delete a file and create another in one commit (for draft -> publish rename)
// extraFiles: optional array of { path, content, encoding } for images etc.
export async function renameFile(oldPath, newPath, content, message, extraFiles = []) {
  const repo = getRepo();
  const refPath = `/repos/${repo}/git/refs/heads/main`;

  for (let attempt = 0; attempt < 3; attempt++) {
    const ref = await request(refPath);
    const baseSha = ref.object.sha;
    const baseCommit = await request(`/repos/${repo}/git/commits/${baseSha}`);
    const baseTreeSha = baseCommit.tree.sha;

    const blob = await request(`/repos/${repo}/git/blobs`, {
      method: 'POST',
      body: JSON.stringify({ content, encoding: 'utf-8' }),
    });

    const treeItems = [
      { path: newPath, mode: '100644', type: 'blob', sha: blob.sha },
      { path: oldPath, mode: '100644', type: 'blob', sha: null },
    ];

    for (const file of extraFiles) {
      const extraBlob = await request(`/repos/${repo}/git/blobs`, {
        method: 'POST',
        body: JSON.stringify({
          content: file.content,
          encoding: file.encoding === 'base64' ? 'base64' : 'utf-8',
        }),
      });
      treeItems.push({ path: file.path, mode: '100644', type: 'blob', sha: extraBlob.sha });
    }

    const tree = await request(`/repos/${repo}/git/trees`, {
      method: 'POST',
      body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems }),
    });

    const commit = await request(`/repos/${repo}/git/commits`, {
      method: 'POST',
      body: JSON.stringify({ message, tree: tree.sha, parents: [baseSha] }),
    });

    try {
      await request(refPath, {
        method: 'PATCH',
        body: JSON.stringify({ sha: commit.sha }),
      });
      return commit;
    } catch (err) {
      if (err.message.includes('422') && attempt < 2) {
        continue;
      }
      throw err;
    }
  }
}
