import assert from 'node:assert/strict';
import fs from 'node:fs';

const file = 'assets/newsletter-popup.js';
const src = fs.readFileSync(file, 'utf8');
const submit = src.match(/addEventListener\(['"]submit['"],[\s\S]*?trapTabCycle\(d\)/)?.[0];
assert.ok(submit, `${file}: no se encuentra el controlador de envío del formulario emergente`);
assert.match(submit, /postNewsletter\s*\(/, `${file}: falta el envío de newsletter`);
assert.match(submit, /submitBtn\.disabled\s*=\s*true/, `${file}: el envío no bloquea el botón durante la solicitud`);
assert.match(submit, /catch\s*\(/, `${file}: falta recuperación ante errores`);
assert.match(submit, /submitBtn\.disabled\s*=\s*false/, `${file}: no se restablece el botón tras un error`);
const lifecycle = /AbortController|\.abort\s*\(|\.isConnected|dialog\?\.open|d\.open|requestVersion|submitVersion|submissionToken|cancelled|canceled/;
assert.ok(lifecycle.test(submit), `${file}: el envío asíncrono no comprueba si su diálogo continúa activo ni dispone de cancelación explícita`);
console.log('OK: ciclo de vida del envío de newsletter revisado');