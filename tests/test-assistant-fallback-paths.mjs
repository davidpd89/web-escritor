import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync('assets/assistant.js', 'utf8');

function section(start, end) {
  const a = source.indexOf(start);
  const b = source.indexOf(end, a + start.length);
  assert.ok(a >= 0 && b > a, `Missing source section: ${start}`);
  return source.slice(a, b);
}

const fallback = section('async function renderSearchFallback(', 'async function queryRemote(');
const remote = section('async function queryRemote(', 'async function submitQuery(');
const submit = source.slice(source.indexOf('async function submitQuery('));

const fallbackChecks = [
  ['local search', /await pagefindFallback\(query\)/],
  ['registry fallback', /await getRegistry\(\)/],
  ['stable navigation sources', /site-map/],
  ['assistant response', /appendMessage\(/],
];

for (const [name, pattern] of fallbackChecks) {
  assert.match(fallback, pattern, `Missing fallback capability: ${name}`);
}

const remoteChecks = [
  ['Turnstile failure', /getTurnstileToken[\s\S]*?catch\s*\{[\s\S]*?renderSearchFallback/],
  ['HTTP failure', /if\s*\(!response\.ok\)[\s\S]*?renderSearchFallback/],
  ['invalid response', /if\s*\(!isValidAssistantResponse\(payload\)\)[\s\S]*?renderSearchFallback/],
  ['transport failure', /catch\s*\(error\)[\s\S]*?renderSearchFallback/],
];

for (const [name, pattern] of remoteChecks) {
  assert.match(remote, pattern, `Missing recovery path: ${name}`);
}

assert.match(submit, /if\s*\(!config\.enabled\)[\s\S]*?renderSearchFallback/, 'Disabled remote service must use local fallback');

console.log('assistant-fallback-paths: OK');
