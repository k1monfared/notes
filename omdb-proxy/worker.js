// Cloudflare Worker: proxies the OMDb API so the browser editor doesn't
// need an OMDb key in localStorage.
//
// Forwards every query string the caller sends, but injects `apikey` from
// the Worker's secret store. Sends permissive CORS so the static site at
// k1monfared.github.io can call it.

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }
    if (request.method !== 'GET') {
      return jsonError(`Method ${request.method} not allowed`, 405);
    }
    if (!env.OMDB_API_KEY) {
      return jsonError('OMDB_API_KEY secret not configured on this Worker', 500);
    }

    const incoming = new URL(request.url);
    const omdbUrl = new URL('https://www.omdbapi.com/');
    for (const [k, v] of incoming.searchParams) {
      // Strip any caller-supplied apikey so the secret can't be overridden
      if (k.toLowerCase() === 'apikey') continue;
      omdbUrl.searchParams.set(k, v);
    }
    omdbUrl.searchParams.set('apikey', env.OMDB_API_KEY);

    try {
      const upstream = await fetch(omdbUrl.toString(), {
        headers: { Accept: 'application/json' },
      });
      const body = await upstream.text();
      return new Response(body, {
        status: upstream.status,
        headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
      });
    } catch (err) {
      return jsonError(`Upstream OMDb fetch failed: ${err.message}`, 502);
    }
  },
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

function jsonError(msg, status) {
  return new Response(JSON.stringify({ Response: 'False', Error: msg }), {
    status,
    headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
  });
}
