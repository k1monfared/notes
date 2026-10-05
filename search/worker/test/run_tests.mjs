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

const DIM = 4;
const DOCS = [
  { i: "a#0", p: "a", u: "a/", t: "matrix tree theorem guide", d: "2024-01-01",
    g: ["math"], l: "en", h: "", a: "", x: "spanning trees of graphs and the matrix tree theorem proof" },
  { i: "b#0", p: "b", u: "b/", t: "cooking pasta", d: "2024-01-02",
    g: ["food"], l: "en", h: "", a: "", x: "boil water add salt and serve" },
  { i: "c#0", p: "c", u: "c/", t: "linear algebra notes", d: "2024-01-03",
    g: ["math"], l: "en", h: "", a: "", x: "eigenvalues and eigenvectors of a matrix" },
];
// One-hot rows so the mock query embedding picks a deterministic winner.
const ROWS = [[100, 0, 0, 0], [0, 100, 0, 0], [0, 0, 100, 0]];

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
      ? { file: "vectors.bin", dtype: "int8", dim: DIM, count: 3,
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
      const row = queryVec[text.replace(prefix, "")] || [0, 0, 0, 1];
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
