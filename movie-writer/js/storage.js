// Local-first storage for movies.log with sync state tracking

const DB_NAME = 'movie-writer';
const DB_VERSION = 2;
let db = null;

function open() {
  if (db) return Promise.resolve(db);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const d = e.target.result;
      if (!d.objectStoreNames.contains('state')) {
        d.createObjectStore('state', { keyPath: 'key' });
      }
      // Clean up old stores from v1
      if (d.objectStoreNames.contains('cache')) {
        d.deleteObjectStore('cache');
      }
    };
    req.onsuccess = (e) => { db = e.target.result; resolve(db); };
    req.onerror = () => reject(req.error);
  });
}

async function put(key, value) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction('state', 'readwrite');
    tx.objectStore('state').put({ key, value });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function get(key) {
  const d = await open();
  return new Promise((resolve, reject) => {
    const tx = d.transaction('state', 'readonly');
    const req = tx.objectStore('state').get(key);
    req.onsuccess = () => resolve(req.result ? req.result.value : null);
    req.onerror = () => reject(req.error);
  });
}

// Movies.log text
export async function getLocalMovies() {
  return get('moviesText');
}

export async function setLocalMovies(text) {
  await put('moviesText', text);
}

// Dirty flag: local changes not yet pushed
export async function isDirty() {
  return (await get('dirty')) === true;
}

export async function setDirty(val) {
  await put('dirty', val);
}

// Pending commit messages (accumulated while offline or between syncs)
export async function getPendingMessages() {
  return (await get('pendingMessages')) || [];
}

export async function addPendingMessage(msg) {
  const msgs = await getPendingMessages();
  msgs.push(msg);
  await put('pendingMessages', msgs);
}

export async function clearPendingMessages() {
  await put('pendingMessages', []);
}
