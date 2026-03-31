// GitHub token management (shares token with blog-writer via same localStorage key)

const TOKEN_KEY = 'gh_token';
const REPO = 'k1monfared/notes';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token.trim());
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return !!getToken();
}

export async function validateToken(token) {
  try {
    const res = await fetch(`https://api.github.com/repos/${REPO}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github.v3+json',
      },
    });
    if (!res.ok) return { valid: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    if (!data.permissions || !data.permissions.push) {
      return { valid: false, error: 'Token lacks write permission for this repo' };
    }
    return { valid: true };
  } catch (err) {
    return { valid: false, error: err.message };
  }
}

export function getRepo() {
  return REPO;
}
