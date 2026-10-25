import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('script.js', 'utf8');
const start = source.indexOf('const NEWSLETTER_EMAIL_RE =');
const end = source.indexOf('function honeypotValue(', start);
assert.ok(start >= 0 && end > start);
const context = vm.createContext({});
vm.runInContext(source.slice(start, end), context);
const valid = value => vm.runInContext('isValidNewsletterEmail(' + JSON.stringify(value) + ')', context);
const cases = [
  ['lector@example.com', true],
  [' lector@example.com ', true],
  ['lector+libros@example.es', true],
  ['', false],
  ['lector', false],
  ['lector@', false],
  ['@example.com', false],
  ['lector@example', false],
  ['lector @example.com', false],
  ['lector@example.com\nmalicioso', false],
  ['a'.repeat(65) + '@example.com', false],
  ['a'.repeat(64) + '@example.com', true],
  ['a@' + 'b'.repeat(250) + '.es', false]
];
for (const [value, expected] of cases) assert.equal(valid(value), expected, `Correo: ${JSON.stringify(value)}`);
console.log('PASS newsletter email boundary matrix');