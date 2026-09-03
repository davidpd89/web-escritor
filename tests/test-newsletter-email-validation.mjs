// isValidEmail() (assets/newsletter-general.js) had zero direct regression
// tests anywhere in the suite -- other newsletter tests check the contract
// around it (no persistence, consistent copy) but never exercised the EMAIL_RE
// regex itself against real edge cases. Loaded via a minimal vm sandbox
// (document.readyState stubbed as "loading" so init() never actually runs,
// since window.DPNewsletterGeneral is exposed before that check).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const code = fs.readFileSync(path.join(__dirname, '../assets/newsletter-general.js'), 'utf8');
const sandbox = { window: {}, document: { readyState: 'loading', addEventListener: () => {} }, location: { hostname: 'davidportodiaz.com' } };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const { isValidEmail } = sandbox.window.DPNewsletterGeneral;

// Unusual but valid addresses a real subscriber might use.
for (const email of [
  'nombre.apellido@example.com',
  'nombre+etiqueta@example.com',
  'a@b.co',
  'usuario@sub.dominio.example.com',
  "o'donnell@example.com",
  'usuario@dominio-con-guion.com',
  'usuario@example.museum',
  'x'.repeat(64) + '@example.com',
]) {
  assert.ok(isValidEmail(email), `debe aceptar «${email}»`);
}

// Invalid addresses (typos/malformed) that must be rejected.
for (const email of [
  '',
  'sin-arroba.example.com',
  'usuario@sin-dominio-con-punto',
  'usuario@@doble-arroba.com',
  'espacio en@medio.com',
  'usuario@',
  '@example.com',
  'usuario@.com',
  'x'.repeat(65) + '@example.com',
  'a@b.c'.padEnd(260, 'x') + '@example.com',
]) {
  assert.ok(!isValidEmail(email), `debe rechazar «${email}»`);
}

console.log('tests/test-newsletter-email-validation: OK');
