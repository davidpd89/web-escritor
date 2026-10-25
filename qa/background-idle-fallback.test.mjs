import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('script.js', 'utf8');
const start = source.indexOf('function scheduleBackgroundIdle(');
const end = source.indexOf('\n}', start);
assert.ok(start >= 0 && end > start);
const definition = source.slice(start, end + 2);
function run(globals) {
  const context = vm.createContext(globals);
  vm.runInContext(definition, context);
  return vm.runInContext('scheduleBackgroundIdle', context);
}
let selected = '';
let priority = '';
let callback = null;
let schedule = run({ scheduler: { postTask(fn, options) { selected = 'scheduler'; priority = options.priority; callback = fn; return 1; } } });
schedule(() => {});
assert.equal(selected, 'scheduler');
assert.equal(priority, 'background');
schedule = run({ requestIdleCallback(fn, options) { selected = 'idle'; callback = fn; assert.equal(options.timeout, 2000); return 2; } });
schedule(() => {});
assert.equal(selected, 'idle');
schedule = run({ setTimeout(fn, delay) { selected = 'timeout'; callback = fn; assert.equal(delay, 200); return 3; } });
schedule(() => {});
assert.equal(selected, 'timeout');
assert.equal(typeof callback, 'function');
console.log('PASS background idle fallback compatibility');
