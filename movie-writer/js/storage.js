// Simple cache for movies.log content

const DB_NAME = 'movie-writer';
const DB_VERSION = 1;
let db = null;

function open() {
  if (db) return Promise.resolve(db);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const d = e.target.result;
      if (!d.objectStoreNames.contains('cache')) {
        d.createObjectStore('cache', { keyPath: 'key' });
      }
    };
    req.onsuccess = (e) => { db = e.target.result; resolve(db); };
    req.onerror = () => reject(req.error);
  });
}

export async function setCache(key, value) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction('cache', 'readwrite');
    tx.objectStore('cache').put({ key, value, timestamp: Date.now() });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getCache(key, maxAge = 5 * 60 * 1000) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction('cache', 'readonly');
    const req = tx.objectStore('cache').get(key);
    req.onsuccess = () => {
      const item = req.result;
      if (!item) { resolve(null); return; }
      if (Date.now() - item.timestamp > maxAge) { resolve(null); return; }
      resolve(item.value);
    };
    req.onerror = () => reject(req.error);
  });
}
