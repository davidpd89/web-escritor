import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const tokens = readFileSync(new URL('../assets/v1-tokens.css', import.meta.url), 'utf8');
const base = readFileSync(new URL('../assets/v1-base.css', import.meta.url), 'utf8');

function get(name) {
  const match = tokens.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`));
  assert.ok(match, `v1-tokens.css: falta ${name}`);
  const value = match[1].trim();
  const ref = value.match(/^var\(--([\w-]+)\)$/);
  return ref ? get(ref[1]) : value;
}

function lum(hex) {
  assert.match(hex, /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i);
  const h = hex.length === 4 ? [...hex.slice(1)].map(x => x + x).join('') : hex.slice(1);
  const c = [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
}

function ratio(a, b) {
  const x = lum(a), y = lum(b);
  return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
}

const text = get('color-on-inverse');
const background = get('surface-inverse');
assert.ok(ratio(text, background) >= 4.5, `Contraste inverso insuficiente: ${ratio(text, background).toFixed(2)}:1`);

for (const selector of ['skip-link', 'primary-action']) {
  const rule = base.match(new RegExp(`html\\.v1 \\.${selector}\\s*\\{([^}]+)\\}`));
  assert.ok(rule, `v1-base.css: falta .${selector}`);
  assert.match(rule[1], /background\s*:\s*var\(--surface-inverse\)/, `.${selector}: fondo inverso no aplicado`);
  assert.match(rule[1], /color\s*:\s*var\(--color-on-inverse\)/, `.${selector}: texto inverso no aplicado`);
}
console.log('PASS: contraste de botones principales y enlace de salto');