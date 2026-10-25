import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('script.js', 'utf8');
const start = source.indexOf('function fallbackCopy(text, done)');
const end = source.indexOf('// Reading progress bar', start);
assert.ok(start >= 0 && end > start, 'No se encontró fallbackCopy');
const code = source.slice(start, end);
let completed = false;
let removed = false;
const textarea = {value: '', style: {}, select() {}};
const document = {
  body: {appendChild() {}, removeChild() {removed = true;}},
  createElement(tag) {assert.equal(tag, 'textarea'); return textarea;},
  execCommand(command) {assert.equal(command, 'copy'); return false;}
};
const context = vm.createContext({document});
vm.runInContext(code, context);
vm.runInContext('fallbackCopy("Texto de prueba", () => { completed = true; })', vm.createContext({document, completed: false}));
// Ejecución aislada con una función de confirmación observable.
const sandbox = {document, mark() {completed = true;}};
vm.runInNewContext(code + '\nfallbackCopy("Texto de prueba", mark);', sandbox);
assert.equal(textarea.value, 'Texto de prueba');
assert.equal(removed, true, 'El textarea temporal debe eliminarse');
assert.equal(completed, false, 'No debe confirmarse una copia que devolvió false');
console.log('PASS clipboard failure state');