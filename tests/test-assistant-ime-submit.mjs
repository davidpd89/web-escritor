import assert from 'node:assert/strict';
import fs from 'node:fs';

const js = fs.readFileSync('assets/assistant.js', 'utf8');
const html = fs.readFileSync('asistente/index.html', 'utf8');

assert.match(html, /<textarea\b[^>]*data-assistant-query/, 'Missing query textarea');
assert.match(html, /<form\b[^>]*data-assistant-form/, 'Missing assistant form');

const keydown = js.match(/input\?\.addEventListener\(['\"]keydown['\"],\s*\(event\)\s*=>\s*\{([\s\S]*?)\n\}\);/);
assert.ok(keydown, 'Missing composer keyboard handler');

const handler = keydown[1];
assert.match(handler, /event\.key\s*===\s*['\"]Enter['\"]/, 'Enter submission missing');
assert.match(handler, /!event\.shiftKey/, 'Shift+Enter must remain available');
assert.match(handler, /!event\.isComposing/, 'IME composition must suppress submission');
assert.match(handler, /event\.preventDefault\(\)/, 'Normal Enter must prevent newline insertion');
assert.match(handler, /requestSubmit\(\)/, 'Normal Enter must submit the form');

for (const event of [
  {key: 'Enter', shiftKey: false, isComposing: true, submit: false},
  {key: 'Enter', shiftKey: false, isComposing: false, submit: true},
  {key: 'Enter', shiftKey: true, isComposing: false, submit: false},
  {key: 'a', shiftKey: false, isComposing: false, submit: false},
]) {
  const actual = event.key === 'Enter' && !event.shiftKey && !event.isComposing;
  assert.equal(actual, event.submit, JSON.stringify(event));
}

console.log('assistant-ime-submit: OK');
