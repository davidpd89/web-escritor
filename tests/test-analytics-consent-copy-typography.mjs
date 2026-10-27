import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const file = 'assets/analytics-consent-banner.js';
const source = readFileSync(file, 'utf8');
const assignment = source.match(/bar\.style\.cssText\s*=\s*(["'`])([\s\S]*?)\1\s*;/);
assert.ok(assignment, `${file}: no se encuentra la declaración visual del aviso`);
const css = assignment[2];
const font = css.match(/(?:^|;)\s*font\s*:\s*(\d+(?:\.\d+)?)px\s*\/\s*(\d+(?:\.\d+)?)/);
assert.ok(font, `${file}: no se puede comprobar el tamaño e interlineado del aviso`);
const size = Number(font[1]);
const lineHeight = Number(font[2]);
assert.ok(size >= 14, `${file}: texto principal del aviso de ${size}px; mínimo recomendado en esta prueba: 14px`);
assert.ok(lineHeight >= 1.4, `${file}: interlineado del aviso ${lineHeight}; mínimo 1.4`);
console.log('analytics-consent-copy-typography: OK');