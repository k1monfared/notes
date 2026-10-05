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
  model?: { id?: string; query_prefix?: string } | null;
  vectors?: { dim?: number; count?: number; model?: string } | null;
};

type Artifacts = {
  key: string;
  docs: Doc[];
  vecs: Int8Array;
  scales: Float32Array;
  dim: number;
};

const RRF_K = 60;
const KW_WEIGHT = 1.0;
const VEC_WEIGHT = 1.15;
// Precision controls: AND needs at least this many chunk hits or the query
// falls back to OR; vector hits below the cosine floor are dropped; the final
// list is capped here.
export const MIN_AND_RESULTS = 5;
export const VECTOR_FLOOR = 0.7;
export const RESULT_CAP = 30;
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

// --- Query operators: +must -not "exact phrase" ---

export type QueryOps = {
  must: string[]; // exact tokens the chunk must contain
  not: string[]; // exact tokens the chunk must not contain
  phrases: string[]; // multi-word spans (space-joined tokens) that must occur
  notPhrases: string[]; // spans that must not occur
  positives: string[]; // must + optional + phrase words, len > 1 (ranking)
  engineTerms: string[]; // every positive word (retrieval)
  vectorText: string; // operator-free text for the embedding
};

function dedup(words: string[]): string[] {
  return [...new Set(words)];
}

export function parseSearchQuery(q: string): QueryOps {
  const must: string[] = [];
  const not: string[] = [];
  const phrases: string[] = [];
  const notPhrases: string[] = [];
  const optional: string[] = [];
  const pushWord = (word: string, target: string[]) => {
    for (const t of tokenize(word)) target.push(t);
  };

  // ([+-]?)"phrase" takes precedence over bare words so +"a b" parses whole.
  const re = /([+-]?)"([^"]+)"|([+-]?)(\S+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(q)) !== null) {
    if (m[2] !== undefined) {
      const joined = tokenize(m[2]).join(" ");
      if (!joined) continue;
      if (m[1] === "-") {
        if (joined.includes(" ")) notPhrases.push(joined);
        else pushWord(joined, not);
      } else {
        if (joined.includes(" ")) phrases.push(joined);
        else pushWord(joined, must);
      }
    } else {
      const pre = m[3];
      if (pre === "+") pushWord(m[4], must);
      else if (pre === "-") pushWord(m[4], not);
      else pushWord(m[4], optional);
    }
  }

  const phraseWords = phrases.flatMap((p) => p.split(" "));
  const engineTerms = dedup([...must, ...optional, ...phraseWords]);
  const positives = engineTerms.filter((t) => t.length > 1);
  const vectorText = dedup([...must, ...optional, ...phrases]).join(" ");
  return { must: dedup(must), not: dedup(not), phrases: dedup(phrases),
    notPhrases: dedup(notPhrases), positives, engineTerms, vectorText };
}

export function chunkMatchesOps(
  doc: Doc, ops: Pick<QueryOps, "must" | "not" | "phrases" | "notPhrases">
): boolean {
  const fields = [doc.t || "", doc.h || "", (doc.g || []).join(" "), doc.x || ""];
  const tokens = new Set<string>();
  const parts: string[] = [];
  for (const f of fields) {
    const tks = tokenize(f);
    tks.forEach((t) => tokens.add(t));
    parts.push(tks.join(" "));
  }
  const joined = parts.join(" ");
  for (const word of ops.must) if (!tokens.has(word)) return false;
  for (const word of ops.not) if (tokens.has(word)) return false;
  for (const p of ops.phrases) if (!joined.includes(p)) return false;
  for (const p of ops.notPhrases) if (joined.includes(p)) return false;
  return true;
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
  // Key on the model and query prefix too, so a manifest-only change (e.g. a
  // new query instruction with identical documents) still refreshes.
  const key = `${content}|${manifest.model?.id || ""}|${manifest.model?.query_prefix || ""}`;
  if (artifacts && artifacts.key === key) return { manifest, artifacts };

  const docsRes = await fetch(siteBase + "docs.json", { cf: { cacheTtl: 300 } });
  if (!docsRes.ok) throw new Error("search index not found");
  const docs = (await docsRes.json()) as Doc[];

  // Keyword-only indexes ship no vectors; the API still answers, lexically.
  if (!manifest.vectors) {
    artifacts = {
      key,
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
  artifacts = { key, docs, ...parsed };
  return { manifest, artifacts };
}

// --- Retrieval ---

export function keywordTopK(
  docs: Doc[], terms: string[], k: number, minAnd: number = MIN_AND_RESULTS
): number[] {
  const scored = new Map<number, { score: number; matched: Set<string> }>();
  docs.forEach((doc, idx) => {
    let score = 0;
    const matched = new Set<string>();
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
        if (tokenSet.has(term)) {
          score += boost;
          matched.add(term);
        } else if (tokens.some((tok) => tok.startsWith(term))) {
          score += boost * 0.5;
          matched.add(term);
        }
      }
    }
    if (score > 0) scored.set(idx, { score, matched });
  });
  let pool = [...scored.entries()];
  if (!terms.length) {
    pool = [];
  } else {
    const anded = pool.filter(([, e]) => e.matched.size >= terms.length);
    if (anded.length >= minAnd) pool = anded;
  }
  return pool
    .sort((a, b) => b[1].score - a[1].score)
    .slice(0, k)
    .map(([idx]) => idx);
}

export function vectorTopK(
  art: Artifacts, qvec: number[], k: number, floor: number = VECTOR_FLOOR
): number[] {
  const scored: Array<[number, number]> = [];
  const { vecs, scales, dim } = art;
  for (let r = 0; r < art.docs.length; r++) {
    const base = r * dim;
    let dot = 0;
    for (let i = 0; i < dim; i++) dot += vecs[base + i] * qvec[i];
    const score = scales[r] * dot;
    if (score >= floor) scored.push([r, score]);
  }
  return scored
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([idx]) => idx);
}

type Fused = { doc: Doc; score: number; arms: Set<string>; semantic: boolean };

export function fuse(
  docs: Doc[], kwIdx: number[], vecIdx: number[], terms: string[],
  ops?: Pick<QueryOps, "must" | "not" | "phrases" | "notPhrases"> | null
): Fused[] {
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
    if (terms.length && hits === terms.length) e.score *= 3.0;
    else if (hits) e.score *= 1.2;
    const when = Date.parse(e.doc.d);
    if (!isNaN(when)) {
      const years = Math.max(0, (now - when) / (365.25 * 24 * 3600 * 1000));
      e.score *= 1 / (1 + 0.03 * years);
    }
  }
  list.sort((a, b) => b.score - a.score);

  const filtered = ops ? list.filter((e) => chunkMatchesOps(e.doc, ops)) : list;

  const seen = new Set<string>();
  const out: Fused[] = [];
  for (const e of filtered) {
    if (seen.has(e.doc.p)) continue;
    seen.add(e.doc.p);
    e.semantic = e.arms.has("vec") && !e.arms.has("kw");
    out.push(e);
    if (out.length >= RESULT_CAP) break;
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
      const { manifest, artifacts: art } = await loadArtifacts(env.SITE_BASE);
      const pq = parseSearchQuery(q);
      if (!pq.engineTerms.length && !pq.phrases.length) {
        return Response.json({ results: [], count: 0, took_ms: Date.now() - started },
          { headers: cors(origin, env) });
      }

      const kwIdx = keywordTopK(art.docs, pq.engineTerms, 50);

      let vecIdx: number[] = [];
      if (art.dim > 0 && pq.vectorText) {
        const prefix = manifest.model?.query_prefix || "";
        const out = (await env.AI.run("@cf/baai/bge-m3", { text: prefix + pq.vectorText })) as { data: number[] };
        const raw = out.data;
        const norm = Math.sqrt(raw.reduce((s, v) => s + v * v, 0)) || 1;
        const qvec = raw.map((v) => v / norm);
        vecIdx = vectorTopK(art, qvec, 50);
      }
      const fused = fuse(art.docs, kwIdx, vecIdx, pq.positives, pq);

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
