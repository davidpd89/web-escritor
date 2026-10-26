import assert from 'node:assert/strict';
import fs from 'node:fs';

const file = 'assets/newsletter-popup.js';
const src = fs.readFileSync(file, 'utf8');
assert.match(src, /if\s*\(shown\s*\|\|\s*dialog\?\.open\)/, `${file}: falta protección frente a aperturas duplicadas`);
assert.match(src, /removeEventListener\(['"]scroll['"],\s*onScroll\)/, `${file}: no se retira el listener de scroll tras abrir`);
assert.match(src, /removeEventListener\(['"]mouseleave['"],\s*onLeave\)/, `${file}: no se retira el listener de salida tras abrir`);
assert.match(src, /addEventListener\(['"]close['"][\s\S]*?\{\s*once:\s*true\s*\}/, `${file}: el listener de cierre debe ejecutarse una sola vez`);
const guardedInit = /window\.__newsletterPopupInitialized|window\.__nlPopupInitialized|document\.getElementById\(['"]nl-popup-dialog['"]\)|document\.querySelector\(['"]#nl-popup-dialog['"]\)/;
assert.ok(guardedInit.test(src), `${file}: no se detecta protección contra la ejecución duplicada del módulo y el registro repetido de listeners globales`);
console.log('OK: idempotencia de listeners de newsletter revisada');