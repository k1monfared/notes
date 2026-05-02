# OMDb proxy (Cloudflare Worker)

A tiny Cloudflare Worker that forwards GET requests to [omdbapi.com](https://www.omdbapi.com/) with the `apikey` query parameter injected from a Worker secret. Lets the browser editor call OMDb without ever holding the key client-side.

## Why

The movies editor at `/movies/` needs to search OMDb and fetch full movie details. Without a backend, it would have to store the OMDb API key in `localStorage` and call OMDb directly. This Worker lets it call a public URL instead, with the secret living in Cloudflare's secret store (which the Worker reads via `env.OMDB_API_KEY`).

## Deploy

You need a Cloudflare account (free tier is fine — 100k requests/day) and `wrangler` installed.

```bash
# 1. Install wrangler
npm install -g wrangler

# 2. Authenticate
wrangler login

# 3. From this directory, set the secret (paste the OMDb key when prompted)
cd omdb-proxy
wrangler secret put OMDB_API_KEY

# 4. Deploy
wrangler deploy
```

Wrangler prints the deployed URL, e.g. `https://omdb-proxy.<your-subdomain>.workers.dev`.

## Wire it up to the editor

Tell the editor to use the proxy by setting one localStorage key:

```js
// Run once in the browser DevTools console on the movies page:
localStorage.setItem('omdb_proxy_url', 'https://omdb-proxy.<your-subdomain>.workers.dev');
// Optional: clear the old direct-OMDb key now that it's not needed
localStorage.removeItem('omdb_api_key');
```

After that, the IMDb picker fetches through your Worker. No more "OMDb API key" prompt; nothing OMDb-related is in browser storage.

## How it works

```
browser ─GET https://omdb-proxy.workers.dev/?s=oslo&y=2021─▶ Worker
                                                              │ inject apikey
                                                              ▼
                                                          omdbapi.com
                                                              │
browser ◀────────────── JSON ─────────────────────────────────┘
```

Permissive CORS (`Access-Control-Allow-Origin: *`) so any browser can call it. The Worker strips any caller-supplied `apikey` before adding the secret, so anyone hitting your Worker uses your free-tier quota — keep an eye on it or tighten the CORS allowlist if abuse becomes a problem.

## Updating the secret

```bash
wrangler secret put OMDB_API_KEY  # overwrites
```

## Removing

```bash
wrangler delete  # removes the Worker
```
