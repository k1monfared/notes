#!/usr/bin/env node
/* Build-time embedding step.
 *
 * Reads a JSON file containing an array of strings, writes a JSON file
 * containing an array of unit-norm float vectors (one per input). Uses the
 * exact model and pooling the browser runtime uses, so build-time document
 * vectors and query-time vectors live in the same space.
 *
 *   node embed.mjs --model <id> --prefix "passage: " \
 *     --input in.json --output out.json [--dtype q8] [--cache dir] [--batch 16]
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pipeline, env } from "@huggingface/transformers";

function parseArgs(argv) {
  const args = { dtype: "q8", batch: 16 };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith("--")) continue;
    const name = key.slice(2);
    const value = argv[i + 1];
    args[name] = value;
    i += 1;
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.model || !args.input || !args.output) {
    console.error("usage: embed.mjs --model <id> --input <json> --output <json>");
    process.exit(1);
  }
  if (args.cache) {
    env.cacheDir = resolve(args.cache);
    mkdirSync(env.cacheDir, { recursive: true });
  }

  const texts = JSON.parse(readFileSync(args.input, "utf8"));
  const prefix = args.prefix || "";
  const batchSize = Number(args.batch) || 16;

  const extractor = await pipeline("feature-extraction", args.model, {
    dtype: args.dtype,
  });

  const vectors = [];
  for (let start = 0; start < texts.length; start += batchSize) {
    const batch = texts.slice(start, start + batchSize).map((t) => prefix + t);
    const output = await extractor(batch, { pooling: "mean", normalize: true });
    const list = output.tolist();
    for (const row of list) vectors.push(row);
    if (process.stderr.isTTY) {
      process.stderr.write(`\rembedded ${vectors.length}/${texts.length}`);
    }
  }
  if (process.stderr.isTTY) process.stderr.write("\n");

  mkdirSync(dirname(resolve(args.output)), { recursive: true });
  writeFileSync(resolve(args.output), JSON.stringify(vectors));
  process.stderr.write(`embedded ${vectors.length} texts -> ${args.output}\n`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
