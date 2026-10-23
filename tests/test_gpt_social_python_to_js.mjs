/** Exact producer -> browser consumer contract. No API calls or secrets. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {visibleSocialMetrics} from '../scripts/research/gpt_social_reader.mjs';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const PYTHON = `
import importlib.util,json
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location('composer','scripts/research/gpt_social_compose.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
b={'id':'bluesky','followers':9,'source':'bluesky-public-appview','status':'ok','observed_at':'2026-10-22T11:00:00Z'}
t={'id':'threads','followers':0,'source':'metricool-mcp-export','status':'ok','observed_at':'2026-10-21'}
print(json.dumps(m.compose([b,t],now=datetime(2026,10,22,12,tzinfo=timezone.utc))))
`;
function produced() {
  const result = spawnSync(process.env.PYTHON ?? 'python', ['-c', PYTHON],
                           {cwd: ROOT, encoding: 'utf8', timeout: 10000});
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  return JSON.parse(result.stdout);
}

test('Python contract carries UTC deadlines and JS accepts the same bytes', () => {
  const json = produced();
  assert.equal(json.totals.valid_until, '2026-10-23T21:59:59Z');
  const output = visibleSocialMetrics(json, Date.parse('2026-10-22T13:00:00Z'));
  assert.equal(output.totals.coverage, 2);
  assert.equal(output.totals.follower_relationships, 9);
});
test('if static JSON is not refreshed the browser drops each counter on time', () => {
  const json = produced();
  const output = visibleSocialMetrics(json, Date.parse('2026-10-23T22:00:00Z'));
  assert.equal(output.totals.coverage, 1);
  assert.equal(output.totals.follower_relationships, 9);
});
test('an indefinitely cached old JSON cannot look like fresh community growth', () => {
  const json = produced();
  const output = visibleSocialMetrics(json, Date.parse('2026-10-25T12:00:00Z'));
  assert.equal(output.totals.coverage, 0);
  assert.equal(output.totals.follower_relationships, null);
});
