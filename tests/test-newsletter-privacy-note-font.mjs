import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const file = 'assets/newsletter-popup.css';
const css = readFileSync(file, 'utf8');
const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(([, selector]) => selector.split(',').some(s => s.trim() === '.nl-popup-consent'));
assert.ok(rules.length, `${file}: falta la regla .nl-popup-consent`);
function declaration(body, property) {
  const pattern = new RegExp('(?:^|;)\\s*' + property + '\\s*:\\s*([^;!}]+)');
  return body.match(pattern)?.[1]?.trim();
}
for (const [, , body] of rules) {
  const font = declaration(body, 'font-size');
  const line = declaration(body, 'line-height');
  assert.ok(font, `${file}: .nl-popup-consent sin tamaño explícito`);
  const match = font.match(/^([\d.]+)(rem|px)$/);
  assert.ok(match, `${file}: tamaño no verificable: ${font}`);
  const px = Number(match[1]) * (match[2] === 'rem' ? 16 : 1);
  assert.ok(px >= 14, `${file}: .nl-popup-consent mide ${px}px; mínimo 14px`);
  assert.ok(line && Number.isFinite(Number(line)) && Number(line) >= 1.4, `${file}: interlineado insuficiente o no verificable: ${line}`);
}
console.log('newsletter-privacy-note-font: OK');