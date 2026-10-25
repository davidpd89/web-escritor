import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync('assets/assistant.js', 'utf8');

const checks = [
  ['request serial increment', /const serial\s*=\s*\+\+requestSerial/],
  ['abort previous request', /activeController\?\.abort\(\)/],
  ['cancel increments generation', /function cancelCurrentRequest[\s\S]*?requestSerial\s*\+=\s*1/],
  ['registry generation guard', /const registry\s*=\s*await getRegistry\(\);\s*if\s*\(serial\s*!==\s*requestSerial\)\s*return/],
  ['remote generation guard', /if\s*\(serial\s*!==\s*requestSerial\)\s*return/],
  ['pending cancellation cleanup', /querySelector\(['\"]\[data-pending=/],
];

for (const [name, pattern] of checks) {
  assert.match(source, pattern, `Missing asynchronous ownership guard: ${name}`);
}

const remote = source.slice(source.indexOf('async function queryRemote('), source.indexOf('async function submitQuery('));
assert.ok(remote.length > 100, 'Remote request implementation missing');

const guardedAppend = remote.lastIndexOf('appendMessage(');
assert.ok(guardedAppend >= 0, 'Remote response does not append messages');

assert.match(remote, /if\s*\(serial\s*!==\s*requestSerial\)\s*return/, 'Remote responses must verify generation');
assert.match(remote, /finally\s*\{[\s\S]*?clearTimeout\(timer\)/, 'Request timeout must be cleared');

console.log('assistant-stale-response-ownership: OK');
