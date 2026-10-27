import assert from 'node:assert/strict';
import fs from 'node:fs';

const file = 'assets/newsletter-popup.js';
const src = fs.readFileSync(file, 'utf8');
const branch = src.match(/if\s*\(result\.ok\s*&&\s*result\.state\s*===\s*['"]pending_confirmation['"]\)\s*\{([\s\S]*?)\}\s*else/)?.[1];
assert.ok(branch, `${file}: no se encuentra la rama de confirmación pendiente`);
assert.match(branch, /copy\.okTitle/, `${file}: falta el título de confirmación`);
assert.match(branch, /copy\.okBody/, `${file}: falta la explicación de confirmación`);
assert.doesNotMatch(branch, /setTimeout\s*\(\s*dismiss\s*,\s*5000\s*\)/, `${file}: la confirmación se cierra automáticamente a los cinco segundos`);
const hasCloseAction = /(?:createElement\(['"]button['"]\)|<button\b|\.addEventListener\(['"]click['"])/.test(branch);
const retainsOriginalControls = !/panel\.innerHTML\s*=/.test(branch);
assert.ok(hasCloseAction || retainsOriginalControls, `${file}: el resultado sustituye los controles del diálogo sin incorporar un cierre explícito`);
console.log('OK: confirmación pendiente persistente y cerrable');