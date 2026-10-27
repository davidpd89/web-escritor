import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const cssFile = 'assets/v1-legal.css';
const htmlFile = 'privacidad.html';
const css = readFileSync(cssFile, 'utf8');
const html = readFileSync(htmlFile, 'utf8');
assert.match(html, /class="legal-toc"/, `${htmlFile}: no existe el índice legal esperado`);
const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(([, selector]) => selector.split(',').some(s => s.trim() === 'html.v1 .legal-toc a'));
assert.ok(rules.length, `${cssFile}: falta la regla tipográfica de enlaces del índice legal`);
for (const [, , body] of rules) {
  const size = body.match(/(?:^|;)\s*font-size\s*:\s*([\d.]+)(rem|px)/);
  if (!size) continue;
  const px = Number(size[1]) * (size[2] === 'rem' ? 16 : 1);
  assert.ok(px >= 14, `${cssFile}: .legal-toc a mide ${px}px; mínimo 14px`);
  const line = body.match(/(?:^|;)\s*line-height\s*:\s*([\d.]+)/);
  assert.ok(line && Number(line[1]) >= 1.35, `${cssFile}: interlineado de .legal-toc a inferior a 1.35 o ausente`);
}
assert.ok(rules.some(([, , body]) => /font-size\s*:/.test(body)), `${cssFile}: ningún tamaño de letra verificable para .legal-toc a`);
console.log('privacy-toc-typography: OK');