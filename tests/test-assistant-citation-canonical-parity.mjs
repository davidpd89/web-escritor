import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const { sources } = JSON.parse(fs.readFileSync(path.join(root, 'data/assistant-source-registry.json'), 'utf8'));
let checked = 0;
for (const source of sources.filter(s => s.visibility === 'public')) {
  const target = new URL(source.url, 'https://davidportodiaz.com');
  const relative = target.pathname.endsWith('/') ? `${target.pathname}index.html` : target.pathname;
  const file = path.join(root, relative.replace(/^\/+/, ''));
  assert.ok(fs.existsSync(file), `${source.id}: source target missing`);
  const html = fs.readFileSync(file, 'utf8');
  const link = [...html.matchAll(/<link\b[^>]*>/gi)].map(m => m[0]).find(tag => /\brel=["']canonical["']/i.test(tag));
  assert.ok(link, `${source.id}: canonical missing`);
  const href = link.match(/\bhref=["']([^"']+)["']/i)?.[1];
  assert.ok(href, `${source.id}: canonical href missing`);
  const canonical = new URL(href, 'https://davidportodiaz.com');
  assert.equal(canonical.origin, target.origin, `${source.id}: canonical cross-origin drift`);
  assert.equal(canonical.pathname, target.pathname, `${source.id}: citation/canonical mismatch`);
  checked++;
}
assert.ok(checked > 0);
console.log(`PASS ${checked} assistant citation canonicals`);
