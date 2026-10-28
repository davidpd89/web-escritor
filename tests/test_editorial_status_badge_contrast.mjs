import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../assets/editoriales.css', import.meta.url), 'utf8');
const tokens = readFileSync(new URL('../assets/v1-tokens.css', import.meta.url), 'utf8');

function token(name) {
  const m = tokens.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`));
  assert.ok(m, `Token ausente: ${name}`);
  const ref = m[1].trim().match(/^var\(--([\w-]+)\)$/);
  return ref ? token(ref[1]) : m[1].trim();
}

function luminance(hex) {
  assert.match(hex, /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i);
  const h = hex.length === 4 ? [...hex.slice(1)].map(c => c + c).join('') : hex.slice(1);
  const c = [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
}

function ratio(a, b) {
  const x = luminance(a), y = luminance(b);
  return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
}

function rule(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const m = css.match(new RegExp(escaped + '\\s*\\{([^}]+)\\}'));
  assert.ok(m, `editoriales.css: falta ${selector}`);
  return m[1];
}

const badge = rule('html.v1 .editorial-badge,html.v1 .editorial-genre');
const open = rule('html.v1 .editorial-badge--open');
const closed = rule('html.v1 .editorial-badge--closed');

assert.doesNotMatch(badge, /(?:^|;)\s*opacity\s*:/, 'editoriales.css: las etiquetas no deben perder opacidad');
assert.doesNotMatch(closed, /(?:^|;)\s*opacity\s*:/, 'editoriales.css: el estado cerrado no debe perder contraste por opacidad');
assert.match(open, /color\s*:\s*var\(--dp-petrol-ink\)/, 'editoriales.css: falta color legible para estado abierto');

for (const [state, color] of [['abierto', token('dp-petrol-ink')], ['cerrado', token('color-muted')]]) {
  const value = ratio(color, token('surface-page'));
  assert.ok(value >= 4.5, `editoriales/: etiqueta ${state}, contraste ${value.toFixed(2)}:1, mínimo 4.5:1`);
}
console.log('PASS: contraste de etiquetas editoriales abiertas y cerradas');