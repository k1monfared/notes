// IndexedDB wrapper for local drafts and image blobs

const DB_NAME = 'blog-writer';
const DB_VERSION = 1;

let db = null;

function open() {
  if (db) return Promise.resolve(db);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const d = e.target.result;
      if (!d.objectStoreNames.contains('drafts')) {
        d.createObjectStore('drafts', { keyPath: 'id' });
      }
      if (!d.objectStoreNames.contains('images')) {
        d.createObjectStore('images', { keyPath: 'id' });
      }
      if (!d.objectStoreNames.contains('cache')) {
        d.createObjectStore('cache', { keyPath: 'key' });
      }
    };
    req.onsuccess = (e) => {
      db = e.target.result;
      resolve(db);
    };
    req.onerror = () => reject(req.error);
  });
}

async function put(store, item) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction(store, 'readwrite');
    tx.objectStore(store).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function get(store, key) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction(store, 'readonly');
    const req = tx.objectStore(store).get(key);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
}

async function getAll(store) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction(store, 'readonly');
    const req = tx.objectStore(store).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

async function remove(store, key) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction(store, 'readwrite');
    tx.objectStore(store).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

// Draft operations
export async function saveDraft(draft) {
  draft.updatedAt = Date.now();
  await put('drafts', draft);
}

export async function getDraft(id) {
  return get('drafts', id);
}

export async function getAllDrafts() {
  return getAll('drafts');
}

export async function deleteDraft(id) {
  await remove('drafts', id);
  // Also clean up associated images
  const images = await getAll('images');
  for (const img of images) {
    if (img.draftId === id) {
      await remove('images', img.id);
    }
  }
}

// Image blob operations
export async function saveImage(image) {
  await put('images', image);
}

export async function getImage(id) {
  return get('images', id);
}

export async function getImagesForDraft(draftId) {
  const all = await getAll('images');
  return all.filter(img => img.draftId === draftId);
}

export async function deleteImage(id) {
  await remove('images', id);
}

// Cache operations (for post list)
export async function setCache(key, value) {
  await put('cache', { key, value, timestamp: Date.now() });
}

export async function getCache(key, maxAge = 5 * 60 * 1000) {
  const item = await get('cache', key);
  if (!item) return null;
  if (Date.now() - item.timestamp > maxAge) return null;
  return item.value;
}
