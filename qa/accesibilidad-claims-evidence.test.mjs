import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const html = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');
const files = fs.readdirSync(path.join(root, 'qa')).filter(name => /\.(mjs|js|py)$/.test(name));
const corpus = files.map(name => ({name, text: fs.readFileSync(path.join(root, 'qa', name), 'utf8')}));

const matrix = [
  {claim: /Navegación por teclado/i, evidence: /keyboard|\.press\(['"]Tab|focus\(/i},
  {claim: /Reflow en anchos de 320 px/i, evidence: /320|horizontal overflow|scrollWidth/i},
  {claim: /movimiento reducido/i, evidence: /prefers-reduced-motion|reducedMotion/i},
  {claim: /sin JavaScript/i, evidence: /javaScriptEnabled:\s*false|No-JS/i},
  {claim: /estructura de encabezados/i, evidence: /heading|h1Count|outline/i},
  {claim: /nombres accesibles/i, evidence: /accessible.name|aria-label|accessibleName/i}
];

test('cada afirmación técnica tiene al menos una prueba rastreable', async t => {
  for (const item of matrix) {
    await t.test(String(item.claim), () => {
      assert.match(html, item.claim, 'La afirmación esperada no está presente');
      const matching = corpus.filter(file => item.evidence.test(file.text));
      assert.ok(matching.length > 0, `No se encontró evidencia para ${item.claim}`);
    });
  }
});