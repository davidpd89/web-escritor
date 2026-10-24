import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const source = await fs.readFile(new URL('../cloudflare-worker-assistant.js',import.meta.url),'utf8');
const instrumented = source + '\nexport { utcDay, secondsUntilUtcMidnight };\n';
const uri = 'data:text/javascript;base64,' + Buffer.from(instrumented).toString('base64');
const {utcDay,secondsUntilUtcMidnight} = await import(uri);

const cases = [
  ['2026-01-01T23:59:59.001Z','2026-01-01',1],
  ['2026-01-02T00:00:00.000Z','2026-01-02',86400],
  ['2026-03-29T23:59:59.001Z','2026-03-29',1],
  ['2026-03-30T00:00:00.000Z','2026-03-30',86400],
  ['2026-10-25T23:59:59.001Z','2026-10-25',1],
  ['2026-10-26T00:00:00.000Z','2026-10-26',86400],
  ['2026-12-31T23:59:59.001Z','2026-12-31',1],
  ['2027-01-01T00:00:00.000Z','2027-01-01',86400],
];
for(const [instant,day,seconds] of cases){
  const now = new Date(instant);
  assert.equal(utcDay(now),day,instant);
  assert.equal(secondsUntilUtcMidnight(now),seconds,instant);
}
for(const instant of ['2026-03-29T01:00:00Z','2026-10-25T01:00:00Z']){
  const now = new Date(instant);
  const seconds = secondsUntilUtcMidnight(now);
  assert.ok(Number.isInteger(seconds) && seconds>=1 && seconds<=86400);
  const next = new Date(now.getTime()+seconds*1000);
  assert.notEqual(utcDay(now),utcDay(next));
}
console.log('PASS assistant UTC quota boundaries');
