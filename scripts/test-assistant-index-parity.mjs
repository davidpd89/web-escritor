import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const registry = JSON.parse(await fs.readFile(path.join(root, "data", "assistant-source-registry.json"), "utf8"));
const generated = await import(`${pathToFileURL(path.join(root, "assets", "assistant-source-registry.js")).href}?v=${Date.now()}`);

assert.deepEqual(generated.ASSISTANT_SOURCE_REGISTRY, registry.sources, "generated assistant registry must exactly match canonical JSON sources");
console.log(`assistant-index-parity: OK (${registry.sources.length} sources)`);
