import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { isSafeInternalPath } from '../assets/assistant-core.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const registry = JSON.parse(fs.readFileSync(path.join(root, 'data/assistant-source-registry.json'), 'utf8'));
const ids = new Set();
const urls = new Set();
let checked = 0;
for (const source of registry.sources) {
  if (source.visibility !== 'public') continue;
  assert.ok(!ids.has(source.id), `duplicate source ID: ${source.id}`);
  ids.add(source.id);
  assert.ok(isSafeInternalPath(source.url), `unsafe source URL: ${source.id} ${source.url}`);
  const url = new URL(source.url, 'https://davidportodiaz.com');
  const pathname = decodeURIComponent(url.pathname);
  assert.ok(!urls.has(pathname), `duplicate canonical target: ${pathname}`);
  urls.add(pathname);
  const relative = pathname.endsWith('/') ? `${pathname}index.html` : pathname;
  const file = path.join(root, relative.replace(/^\/+/, ''));
  assert.ok(fs.existsSync(file) && fs.statSync(file).isFile(), `${source.id}: missing target ${relative}`);
  assert.match(fs.readFileSync(file, 'utf8'), /<main\b/i, `${source.id}: target lacks main content`);
  checked++;
}
assert.ok(checked >= 15, `unexpectedly small public registry: ${checked}`);
console.log(`PASS ${checked} assistant public source targets`);
