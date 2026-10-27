import assert from 'node:assert/strict';
import fs from 'node:fs';

const popupFile = 'assets/newsletter-popup.js';
const popup = fs.readFileSync(popupFile, 'utf8');
const script = fs.readFileSync('script.js', 'utf8');
const submit = popup.match(/addEventListener\(['"]submit['"],[\s\S]*?trapTabCycle\(d\)/)?.[0];
assert.ok(submit, `${popupFile}: falta el controlador del formulario`);
assert.match(submit, /statusEl\.textContent\s*=\s*newsletterErrorMessage\(/, `${popupFile}: el error debe representarse como texto`);
assert.match(script, /function newsletterErrorMessage\s*\(/, 'script.js: falta la traducción de errores a mensajes controlados');
assert.doesNotMatch(submit, /(?:statusEl|emailEl)\.innerHTML\s*=/, `${popupFile}: un valor de formulario o mensaje de error no debe introducirse mediante innerHTML`);
const success = submit.match(/if\s*\(result\.ok\s*&&[\s\S]*?\}\s*else/)?.[0];
assert.ok(success, `${popupFile}: no se encuentra el resultado de confirmación`);
assert.doesNotMatch(success, /panel\.innerHTML\s*=/, `${popupFile}: la confirmación utiliza innerHTML; emplear replaceChildren y textContent para evitar futuras interpolaciones inseguras`);
console.log('OK: destinos DOM de mensajes de conversión revisados');