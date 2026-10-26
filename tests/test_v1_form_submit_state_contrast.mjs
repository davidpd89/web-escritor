import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../assets/v1-base.css', import.meta.url), 'utf8');
const tokens = readFileSync(new URL('../assets/v1-tokens.css', import.meta.url), 'utf8');

function get(name) {
  const m = tokens.match(new RegExp(`--${name}\\s*:\\s*([^;]+);`));
  assert.ok(m, `Falta --${name}`);
  const value = m[1].trim();
  const ref = value.match(/^var\(--([\w-]+)\)$/);
  return ref ? get(ref[1]) : value;
}

function lum(hex) {
  assert.match(hex, /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i);
  const h = hex.length === 4 ? [...hex.slice(1)].map(x => x + x).join('') : hex.slice(1);
  const v = [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
  return .2126 * v[0] + .7152 * v[1] + .0722 * v[2];
}

function contrast(a, b) {
  const x = lum(a), y = lum(b);
  return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
}

const normal = css.match(/html\.v1 \.form-submit\s*\{([^}]+)\}/);
const interactive = css.match(/html\.v1 \.form-submit:hover,html\.v1 \.form-submit:focus-visible\s*\{([^}]+)\}/);
assert.ok(normal, 'v1-base.css: falta regla de botón de envío');
assert.ok(interactive, 'v1-base.css: faltan estados hover/focus-visible');
assert.match(normal[1], /background\s*:\s*var\(--color-accent-strong\)/);
assert.match(normal[1], /color\s*:\s*#fff\b/i);
assert.match(interactive[1], /background\s*:\s*color-mix\(in srgb,var\(--color-accent-strong\) 85%,black\)/);

const background = get('color-accent-strong');
const ratio = contrast('#ffffff', background);
assert.ok(ratio >= 4.5, `Formulario: contraste normal ${ratio.toFixed(2)}:1; mínimo 4.5:1`);

const darkened = '#' + [0, 2, 4].map(i => Math.round(parseInt(background.slice(1).slice(i, i + 2), 16) * .85).toString(16).padStart(2, '0')).join('');
const hoverRatio = contrast('#ffffff', darkened);
assert.ok(hoverRatio >= 4.5, `Formulario: contraste hover/foco ${hoverRatio.toFixed(2)}:1; mínimo 4.5:1`);
assert.ok(hoverRatio >= ratio, 'Formulario: hover/foco no debe empeorar el contraste');
console.log('PASS: contraste de botones de formulario y estados interactivos');