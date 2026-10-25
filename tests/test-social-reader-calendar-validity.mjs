import test from 'node:test';
import assert from 'node:assert/strict';
import {visibleSocialMetrics} from '../scripts/research/gpt_social_reader.mjs';

const NOW = Date.parse('2026-10-23T12:00:00Z');
const base = () => ({schema_version:1, generated_at:'2026-10-23T11:00:00Z',
  networks:[{id:'threads', source:'metricool-mcp-export', status:'ok', followers:11,
    observed_at:'2026-10-22', valid_until:'2026-10-24T11:00:00Z'}]});

for (const stamp of ['2026-02-30', '2026-13-01', '2026-10-32', '2026-02-30T10:00:00Z']) {
  test(`impossible dates never become displayed evidence: ${stamp}`, () => {
    const payload = base(); payload.networks[0].observed_at = stamp;
    assert.equal(visibleSocialMetrics(payload, NOW).networks[2].followers, null);
  });
}
