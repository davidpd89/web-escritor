import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('script.js', 'utf8');
const end = source.indexOf('// Client contract');
assert.ok(end > 0);
const code = source.slice(0, end);
const cases = [
  {name: 'sin APIs', globals: {}},
  {name: 'requestIdleCallback', globals: {requestIdleCallback: fn => {queueMicrotask(fn); return 1;}}},
  {name: 'Scheduler API', globals: {scheduler: {postTask: fn => Promise.resolve().then(fn)}}}
];
for (const test of cases) {
  let calls = 0;
  const context = vm.createContext({...test.globals, Promise, setTimeout: fn => {queueMicrotask(fn); return 1;}});
  vm.runInContext(code, context);
  context.runTask = () => {calls++;};
  await vm.runInContext('scheduleTask(() => runTask())', context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls, 1, `${test.name}: scheduleTask`);
  calls = 0;
  vm.runInContext('scheduleBackgroundIdle(() => runTask())', context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls, 1, `${test.name}: scheduleBackgroundIdle`);
}
console.log('PASS scheduler fallback contract');