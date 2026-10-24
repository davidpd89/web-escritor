import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('cuaderno');
const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const ledger = index.match(/<section class="cuaderno-feature"[\s\S]*?<\/section>/)?.[0] + (index.match(/<ol class="cuaderno-ledger">[\s\S]*?<\/ol>/)?.[0] || '');
assert.ok(ledger && !ledger.startsWith('undefined'), 'No se encuentra inventario editorial');
const dirs = fs.readdirSync(root, { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'temas');
let active = 0;
for (const dir of dirs) {
  const rel = `/cuaderno/${dir.name}/`;
  const file = path.join(root, dir.name, 'index.html');
  assert.ok(fs.existsSync(file), `${rel}: falta index.html`);
  const html = fs.readFileSync(file, 'utf8');
  const article = /"@type"\s*:\s*"Article"/.test(html);
  const linked = ledger.includes(`href="${rel}"`);
  if (article) {
    active++;
    assert.ok(linked, `${rel}: Article ausente del archivo`);
  } else {
    assert.ok(!linked, `${rel}: página no Article promocionada como artículo vigente`);
  }
}
assert.ok(active >= 5, `Censo anormalmente bajo: ${active}`);
console.log(`OK: ${active} artículos vigentes presentes en el archivo`);
