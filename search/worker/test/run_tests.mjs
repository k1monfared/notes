#!/usr/bin/env node
/* Pre-deploy Worker tests. Compiles worker.ts, then drives the real request
 * handler with mocked artifact fetch and AI embeddings. No network, no
 * Cloudflare account needed. Fails non-zero on the first broken expectation.
 *
 * Covers past deploy-then-discover bugs: exact-title ranking, CORS origins,
 * keyword-only manifests, and manifest refresh without new documents.
 */
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const here = dirname(fileURLToPath(import.meta.url));
const workerDir = resolve(here, "..");
const outDir = mkdtempSync(join(tmpdir(), "notes-search-test-"));

const DIM = 5;
const DOCS = [
  { i: "a#0", p: "a", u: "a/", t: "matrix tree theorem guide", d: "2024-01-01",
    g: ["math"], l: "en", h: "", a: "", x: "spanning trees of graphs and the matrix tree theorem proof" },
  { i: "b#0", p: "b", u: "b/", t: "cooking pasta", d: "2024-01-02",
    g: ["food"], l: "en", h: "", a: "", x: "boil water add salt and serve" },
  { i: "c#0", p: "c", u: "c/", t: "linear algebra notes", d: "2024-01-03",
    g: ["math", "linear algebra"], l: "en", h: "", a: "", x: "eigenvalues and eigenvectors of a matrix" },
  { i: "d#0", p: "d", u: "d/", t: "یک غزل بهاری", d: "2023-05-05",
    g: ["poem"], l: "fa", h: "", a: "", x: "شعر درباره بهار و شکوفه" },
];
// One-hot rows so the mock query embedding picks a deterministic winner.
// The fifth dimension matches nothing, for testing the similarity floor.
const ROWS = [[100, 0, 0, 0, 0], [0, 100, 0, 0, 0], [0, 0, 100, 0, 0], [0, 0, 0, 100, 0]];

function vectorsBin() {
  const buf = new ArrayBuffer(16 + 4 * ROWS.length + DIM * ROWS.length);
  const dv = new DataView(buf);
  dv.setUint8(0, "N".charCodeAt(0));
  dv.setUint8(1, "S".charCodeAt(0));
  dv.setUint8(2, "E".charCodeAt(0));
  dv.setUint8(3, "V".charCodeAt(0));
  dv.setUint32(4, 1, true);
  dv.setUint32(8, ROWS.length, true);
  dv.setUint32(12, DIM, true);
  let off = 16;
  for (const _r of ROWS) { dv.setFloat32(off, 1.0, true); off += 4; }
  const bytes = new Int8Array(buf, off);
  ROWS.flat().forEach((v, i) => { bytes[i] = v; });
  return buf;
}

function manifestDoc(prefix, withVectors = true) {
  return {
    schema: 1, source: "blog", generated: "2024-01-01T00:00:00Z",
    content: "fixture-content",
    counts: { posts: 3, chunks: 3 },
    model: { id: "test-model", dim: DIM, query_prefix: prefix, passage_prefix: "" },
    vectors: withVectors
      ? { file: "vectors.bin", dtype: "int8", dim: DIM, count: 4,
          model: "test-model", backend: "test", api: "" }
      : null,
    fields: { indexed: ["t", "h", "g", "x"], stored: ["p"] },
  };
}

let prefix = "INSTR: ";
let serveVectors = true;
let capturedQuery = null;
const queryVec = { "matrix tree theorem": ROWS[0], "gossip rumors": ROWS[1] };

const SITE = "https://example.test/search/";
globalThis.fetch = async (url) => {
  const name = String(url).slice(SITE.length);
  if (name === "manifest.json") {
    return new Response(JSON.stringify(manifestDoc(prefix, serveVectors)));
  }
  if (name === "docs.json") return new Response(JSON.stringify(DOCS));
  if (name === "vectors.bin") {
    if (!serveVectors) return new Response("nope", { status: 404 });
    return new Response(vectorsBin());
  }
  throw new Error("unexpected fetch: " + url);
};

const env = {
  AI: {
    run: async (_model, { text }) => {
      capturedQuery = text;
      const row = queryVec[text.replace(prefix, "")] || [0, 0, 0, 0, 1];
      const norm = Math.hypot(...row) || 1;
      return { data: row.map((v) => v / norm) };
    },
  },
  ALLOWED_ORIGINS: "https://k1monfared.github.io, https://k1monfared.com",
  SITE_BASE: SITE,
};

execFileSync("npx", ["tsc", "-p", "tsconfig.json", "--outDir", outDir,
  "--noEmit", "false"], { cwd: workerDir, stdio: "pipe" });
const worker = (await import(join(outDir, "worker.js"))).default;

async function call(path, origin = "https://k1monfared.com") {
  const headers = origin ? { Origin: origin } : {};
  const res = await worker.fetch(new Request("https://w.test" + path, { headers }), env);
  return { status: res.status, acao: res.headers.get("access-control-allow-origin"),
           json: await res.json() };
}

let n = 0;
const check = (name, cond) => {
  n += 1;
  assert.ok(cond, `FAILED: ${name}`);
  console.log(`ok ${n} - ${name}`);
};

// Error paths and CORS behavior.
check("health 200", (await call("/health")).status === 200);
check("missing q is 400", (await call("/search")).status === 400);
check("unknown scope is 400", (await call("/search?q=x&scope=nope")).status === 400);
check("allowed origin gets ACAO",
  (await call("/search?q=x", "https://k1monfared.com")).acao === "https://k1monfared.com");
check("disallowed origin gets no ACAO",
  (await call("/search?q=x", "https://evil.example")).acao === null);
const opt = await worker.fetch(
  new Request("https://w.test/search", { method: "OPTIONS", headers: { Origin: "https://k1monfared.com" } }), env);
check("preflight 204 with ACAO", opt.status === 204);

// Exact title match must win (past ranking regression).
const exact = await call("/search?q=matrix%20tree%20theorem&scope=blog");
check("hybrid 200", exact.status === 200);
check("exact title match ranks first",
  exact.json.results[0] && exact.json.results[0].t === "matrix tree theorem guide");
check("query carried the instruction prefix", capturedQuery === "INSTR: matrix tree theorem");

// Pure-vector query surfaces with the semantic flag.
const sem = await call("/search?q=gossip%20rumors&scope=blog");
check("semantic-only query finds the vector match",
  sem.json.results[0] && sem.json.results[0].t === "cooking pasta");
check("vector-only hit is flagged semantic", sem.json.results[0].semantic === true);

// Precision controls, tested directly against the exported retrieval fns.
const lib = await import(join(outDir, "worker.js"));
check("strict AND keeps only full matches",
  JSON.stringify(lib.keywordTopK(DOCS, ["matrix", "theorem"], 50, 1)) === "[0]");
const fb = lib.keywordTopK(DOCS, ["matrix", "theorem"], 50);
check("AND fallback includes partial matches", fb.includes(0) && fb.includes(2));
const art = { docs: DOCS, vecs: new Int8Array(ROWS.flat()),
  scales: new Float32Array([1, 1, 1, 1]), dim: DIM };
check("floor drops weak vector hits",
  lib.vectorTopK(art, [0, 0, 0, 0, 1], 50).length === 0);
check("strong vector hit survives the floor",
  JSON.stringify(lib.vectorTopK(art, [1, 0, 0, 0, 0], 50)) === "[0]");
const many = Array.from({ length: 40 }, (_, i) => (
  { ...DOCS[0], i: `x#${i}`, p: `x${i}`, t: `post ${i} zzz`, x: "zzz zzz" }));
check("results capped at 30",
  lib.fuse(many, many.map((_, i) => i), [], ["zzz"]).length === 30);

// Operators: parsing, required/excluded terms, exact phrases.
const pq = lib.parseSearchQuery('+latex -book "tex editor" cooking');
check("parse +must", JSON.stringify(pq.must) === '["latex"]');
check("parse -not", JSON.stringify(pq.not) === '["book"]');
check("parse quoted phrase", JSON.stringify(pq.phrases) === '["tex editor"]');
check("vector text excludes negations", pq.vectorText.indexOf("book") < 0);

const excl = await call("/search?q=" + encodeURIComponent("+matrix -theorem") + "&scope=blog");
check("excluded term drops the hit",
  excl.json.results.length === 1 && excl.json.results[0].t === "linear algebra notes");
const adjMiss = await call("/search?q=" + encodeURIComponent('"trees graphs"') + "&scope=blog");
check("non-adjacent words fail the phrase", adjMiss.json.count === 0);
const adjHit = await call("/search?q=" + encodeURIComponent('"tree theorem"') + "&scope=blog");
check("adjacent words satisfy the phrase",
  adjHit.json.results.length > 0 && adjHit.json.results[0].t === "matrix tree theorem guide");

// Facets: parsing, tag/lang/date filtering, facet-only browsing.
const fp = lib.parseSearchQuery('tag:math lang:FA after:2024 before:2025');
check("parse tag facet", JSON.stringify(fp.tags) === '["math"]');
check("parse lang facet lowercased", JSON.stringify(fp.langs) === '["fa"]');
check("parse after date", fp.after === "2024-01-01");
check("parse before date", fp.before === "2025-01-01");
check("facets are not search words", fp.engineTerms.length === 0);
const fq = lib.parseSearchQuery('tag:"linear algebra" -tag:food after:soon');
check("parse quoted multi-word tag", JSON.stringify(fq.tags) === '["linear algebra"]');
check("parse negated tag", JSON.stringify(fq.notTags) === '["food"]');
check("invalid date degrades to words", fq.after === null && fq.engineTerms.includes("after"));

async function titles(path) {
  const r = await call(path);
  return (r.json.results || []).map((d) => d.t).sort();
}
check("tag:math scopes to tagged posts",
  JSON.stringify(await titles("/search?q=tag%3Amath&scope=blog")) ===
  JSON.stringify(["linear algebra notes", "matrix tree theorem guide"]));
check("quoted multi-word tag matches",
  JSON.stringify(await titles("/search?q=tag%3A%22linear+algebra%22&scope=blog")) ===
  JSON.stringify(["linear algebra notes"]));
check("lang:fa scopes by language",
  JSON.stringify(await titles("/search?q=lang%3Afa&scope=blog")) === JSON.stringify(["یک غزل بهاری"]));
const afterTitles = await titles("/search?q=after%3A2024&scope=blog");
check("after: filters old posts out",
  afterTitles.length === 3 && !afterTitles.includes("یک غزل بهاری"));
check("before: keeps only old posts",
  JSON.stringify(await titles("/search?q=before%3A2024&scope=blog")) === JSON.stringify(["یک غزل بهاری"]));
check("facets combine with terms",
  JSON.stringify(await titles("/search?q=matrix+tag%3Amath&scope=blog")) ===
  JSON.stringify(["linear algebra notes", "matrix tree theorem guide"]));
check("negated facet browses the rest",
  (await titles("/search?q=-tag%3Afood&scope=blog")).length === 3);

// Manifest-only change (new prefix, same documents) must refresh.
prefix = "INSTR2: ";
await call("/search?q=matrix%20tree%20theorem&scope=blog");
check("prefix change takes effect without new documents",
  capturedQuery === "INSTR2: matrix tree theorem");

// Keyword-only manifests still answer.
serveVectors = false;
prefix = "INSTR2: ";
const kw = await call("/search?q=matrix%20tree%20theorem&scope=blog");
check("keyword-only mode 200", kw.status === 200);
check("keyword-only finds the title match",
  kw.json.results[0] && kw.json.results[0].t === "matrix tree theorem guide");

// Deployed config must allowlist the real site origins (past CORS outage).
const toml = readFileSync(join(workerDir, "wrangler.toml"), "utf8");
const allowed = (toml.match(/ALLOWED_ORIGINS\s*=\s*"([^"]*)"/) || [])[1] || "";
check("wrangler allowlists github.io origin", allowed.includes("https://k1monfared.github.io"));
check("wrangler allowlists canonical domain", allowed.includes("https://k1monfared.com"));
check("site base ends with slash", /SITE_BASE\s*=\s*"[^"]+\/"/.test(toml));

// Keep a copy of the compiled worker for debugging failures.
writeFileSync(join(outDir, "fixture-docs.json"), JSON.stringify(DOCS));
console.log(`\nall ${n} worker tests passed`);
