import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const file = 'assets/newsletter-popup.css';
const css = readFileSync(file, 'utf8');
const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
const declarations = rules.filter(([, selector]) => selector.split(',').some(s => s.trim() === '#nl-popup-email')).flatMap(([, , body]) => [...body.matchAll(/(?:^|;)\s*font-size\s*:\s*([^;!}]+)/g)].map(m => m[1].trim()));
assert.ok(declarations.length, `${file}: falta font-size explícito para #nl-popup-email`);
function pixels(value) {
  const match = value.match(/^([\d.]+)(px|rem)$/);
  assert.ok(match, `${file}: unidad tipográfica no verificable: ${value}`);
  return Number(match[1]) * (match[2] === 'rem' ? 16 : 1);
}
for (const value of declarations) {
  assert.ok(pixels(value) >= 16, `${file}: #nl-popup-email usa ${value} (${pixels(value)}px); mínimo 16px para evitar zoom automático en Safari iOS`);
}
console.log('newsletter-popup-ios-font: OK');