import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../assets/v1-tokens.css', import.meta.url), 'utf8');

function token(name) {
  const match = css.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`));
  assert.ok(match, `v1-tokens.css: falta --${name}`);
  return match[1].trim();
}

function resolve(value, seen = new Set()) {
  const match = value.match(/^var\(--([\w-]+)\)$/);
  if (!match) return value;
  assert.ok(!seen.has(match[1]), `Referencia circular: ${match[1]}`);
  seen.add(match[1]);
  return resolve(token(match[1]), seen);
}

function rgb(value) {
  const hex = resolve(value);
  assert.match(hex, /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i, `Color no hexadecimal: ${hex}`);
  const full = hex.length === 4 ? [...hex.slice(1)].map(x => x + x).join('') : hex.slice(1);
  return [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16) / 255);
}

function luminance(value) {
  const channels = rgb(value).map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function contrast(a, b) {
  const x = luminance(a), y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

const surface = token('surface-page');
for (const name of ['color-text', 'color-muted', 'color-accent', 'color-accent-strong', 'color-accent-hover']) {
  const ratio = contrast(token(name), surface);
  assert.ok(ratio >= 4.5, `v1-tokens.css: --${name} sobre --surface-page tiene contraste ${ratio.toFixed(2)}:1; mínimo 4.5:1`);
}
console.log('PASS: contraste AA de tokens editoriales de texto y enlaces');