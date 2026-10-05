/**
 * notes-search: hybrid search API for the static notes sites.
 *
 * The visitor sends only the query string. The Worker loads the already
 * public docs.json + vectors.bin (single source of truth, no separate upload
 * step), embeds the query with Workers AI (multilingual bge-m3), scores the
 * keyword and vector arms, fuses with Reciprocal Rank Fusion, and returns the
 * top results as JSON. The browser renders them with the same UI it uses for
 * local search, and falls back to client-side keyword search if this API is
 * unreachable.
 *
 * Required bindings in wrangler.toml:
 *   AI               Workers AI binding
 *   ALLOWED_ORIGINS  comma-separated origins allowed to call this API (vars)
 *   SITE_BASE        public base URL of the source index, ending in / (vars)
 */

export interface Env {
  AI: Ai;
  ALLOWED_ORIGINS: string;
  SITE_BASE: string;
}

type Doc = {
  i: string;
  p: string;
  u: string;
  t: string;
  d: string;
  g: string[];
  l: string;
  h: string;
  a: string;
  x: string;
};

type Manifest = {
  generated?: string;
  content?: string;
  vectors?: { dim?: number; count?: number; model?: string } | null;
};

type Artifacts = {
  content: string;
  docs: Doc[];
  vecs: Int8Array;
  scales: Float32Array;
  dim: number;
};

const RRF_K = 60;
const KW_WEIGHT = 1.0;
const VEC_WEIGHT = 1.15;
const FIELD_BOOSTS: Array<[string, number]> = [
  ["t", 3],
  ["h", 2],
  ["g", 2],
  ["x", 1],
];

// In-isolate cache. Refreshed only when the published content hash changes.
let artifacts: Artifacts | null = null;

// --- Text normalization (mirrors search/text.py and search.js) ---

function normalizeFa(s: string): string {
  return s
    .normalize("NFKC")
    .replace(/[ً-ٰٟ]/g, "")
    .replace(/ـ/g, "")
    .replace(/ك/g, "ک")
    .replace(/ڪ/g, "ک")
    .replace(/ي/g, "ی")
    .replace(/ى/g, "ی")
    .replace(/[‌-‏‪-‮﻿]/g, "");
}

function tokenize(text: string): string[] {
  return normalizeFa(text)
    .toLowerCase()
    .split(/[\s\p{P}\p{S}]+/u)
    .filter((t) => t.length > 0);
}

// --- Artifacts ---

function parseVectors(buf: ArrayBuffer): { vecs: Int8Array; scales: Float32Array; dim: number } {
  const dv = new DataView(buf);
  const magic = String.fromCharCode(dv.getUint8(0), dv.getUint8(1), dv.getUint8(2), dv.getUint8(3));
  if (magic !== "NSEV") throw new Error("bad vectors file");
  const count = dv.getUint32(8, true);
  const dim = dv.getUint32(12, true);
  const scales = new Float32Array(count);
  let off = 16;
  for (let i = 0; i < count; i++) {
    scales[i] = dv.getFloat32(off, true);
    off += 4;
  }
  const vecs = new Int8Array(buf, off, count * dim);
  return { vecs, scales, dim };
}

async function loadArtifacts(siteBase: string): Promise<{ manifest: Manifest; artifacts: Artifacts }> {
  const manRes = await fetch(siteBase + "manifest.json", { cf: { cacheTtl: 60 } });
  if (!manRes.ok) throw new Error("search manifest not found");
  const manifest = (await manRes.json()) as Manifest;
  const content = manifest.content || manifest.generated || "";
  if (artifacts && artifacts.content === content) return { manifest, artifacts };

  const docsRes = await fetch(siteBase + "docs.json", { cf: { cacheTtl: 300 } });
  if (!docsRes.ok) throw new Error("search index not found");
  const docs = (await docsRes.json()) as Doc[];

  // Keyword-only indexes ship no vectors; the API still answers, lexically.
  if (!manifest.vectors) {
    artifacts = {
      content,
      docs,
      vecs: new Int8Array(0),
      scales: new Float32Array(0),
      dim: 0,
    };
    return { manifest, artifacts };
  }

  const vecRes = await fetch(siteBase + "vectors.bin", { cf: { cacheTtl: 300 } });
  if (!vecRes.ok) throw new Error("search vectors not found");
  const parsed = parseVectors(await vecRes.arrayBuffer());
  artifacts = { content, docs, ...parsed };
  return { manifest, artifacts };
}

// --- Retrieval ---

function keywordScores(docs: Doc[], terms: string[]): Map<number, number> {
  const scores = new Map<number, number>();
  docs.forEach((doc, idx) => {
    let score = 0;
    const fields: Record<string, string> = {
      t: doc.t || "",
      h: doc.h || "",
      g: (doc.g || []).join(" "),
      x: doc.x || "",
    };
    for (const [field, boost] of FIELD_BOOSTS) {
      const tokens = tokenize(fields[field]);
      const tokenSet = new Set(tokens);
      for (const term of terms) {
        if (tokenSet.has(term)) score += boost;
        else if (tokens.some((tok) => tok.startsWith(term))) score += boost * 0.5;
      }
    }
    if (score > 0) scores.set(idx, score);
  });
  return scores;
}

function topEntries(scores: Map<number, number>, k: number): number[] {
  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([idx]) => idx);
}

function vectorScores(art: Artifacts, qvec: number[]): Map<number, number> {
  const scores = new Map<number, number>();
  const { vecs, scales, dim } = art;
  for (let r = 0; r < art.docs.length; r++) {
    const base = r * dim;
    let dot = 0;
    for (let i = 0; i < dim; i++) dot += vecs[base + i] * qvec[i];
    scores.set(r, scales[r] * dot);
  }
  return scores;
}

type Fused = { doc: Doc; score: number; arms: Set<string>; semantic: boolean };

function fuse(docs: Doc[], kwIdx: number[], vecIdx: number[], terms: string[]): Fused[] {
  const map = new Map<string, Fused>();
  const add = (idx: number, rank: number, arm: string, weight: number) => {
    const doc = docs[idx];
    let e = map.get(doc.i);
    if (!e) {
      e = { doc, score: 0, arms: new Set(), semantic: false };
      map.set(doc.i, e);
    }
    e.score += weight / (RRF_K + rank + 1);
    e.arms.add(arm);
  };
  kwIdx.forEach((idx, rank) => add(idx, rank, "kw", KW_WEIGHT));
  vecIdx.forEach((idx, rank) => add(idx, rank, "vec", VEC_WEIGHT));

  const list = [...map.values()];
  const now = Date.now();
  for (const e of list) {
    const title = tokenize(e.doc.t || "").join(" ");
    const hits = terms.filter((t) => title.includes(t)).length;
    if (terms.length && hits === terms.length) e.score *= 1.6;
    else if (hits) e.score *= 1.2;
    const when = Date.parse(e.doc.d);
    if (!isNaN(when)) {
      const years = Math.max(0, (now - when) / (365.25 * 24 * 3600 * 1000));
      e.score *= 1 / (1 + 0.03 * years);
    }
  }
  list.sort((a, b) => b.score - a.score);

  const seen = new Set<string>();
  const out: Fused[] = [];
  for (const e of list) {
    if (seen.has(e.doc.p)) continue;
    seen.add(e.doc.p);
    e.semantic = e.arms.has("vec") && !e.arms.has("kw");
    out.push(e);
    if (out.length >= 25) break;
  }
  return out;
}

// --- HTTP ---

function cors(origin: string | null, env: Env): Record<string, string> {
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (origin && allowed.includes(origin)) headers["Access-Control-Allow-Origin"] = origin;
  return headers;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin");

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          ...cors(origin, env),
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    if (url.pathname === "/health") {
      return Response.json({ ok: true }, { headers: cors(origin, env) });
    }

    if (url.pathname !== "/search" || request.method !== "GET") {
      return Response.json({ error: "not found" }, { status: 404, headers: cors(origin, env) });
    }

    const q = (url.searchParams.get("q") || "").trim();
    const scope = url.searchParams.get("scope") || "blog";
    if (!q) {
      return Response.json({ error: "missing q" }, { status: 400, headers: cors(origin, env) });
    }
    if (scope !== "blog") {
      return Response.json({ error: "unknown scope" }, { status: 400, headers: cors(origin, env) });
    }

    const started = Date.now();
    try {
      const { artifacts: art } = await loadArtifacts(env.SITE_BASE);
      const terms = tokenize(q).filter((t) => t.length > 1);

      const kwIdx = topEntries(keywordScores(art.docs, terms), 50);

      let vecIdx: number[] = [];
      if (art.dim > 0) {
        const out = (await env.AI.run("@cf/baai/bge-m3", { text: q })) as { data: number[] };
        const raw = out.data;
        const norm = Math.sqrt(raw.reduce((s, v) => s + v * v, 0)) || 1;
        const qvec = raw.map((v) => v / norm);
        vecIdx = topEntries(vectorScores(art, qvec), 50);
      }
      const fused = fuse(art.docs, kwIdx, vecIdx, terms);

      return Response.json(
        {
          results: fused.map((e) => ({ ...e.doc, semantic: e.semantic })),
          count: fused.length,
          took_ms: Date.now() - started,
        },
        { headers: cors(origin, env) }
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "search failed";
      return Response.json({ error: message }, { status: 500, headers: cors(origin, env) });
    }
  },
} satisfies ExportedHandler<Env>;
