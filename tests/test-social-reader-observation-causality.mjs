import test from 'node:test';
import assert from 'node:assert/strict';
import {visibleSocialMetrics} from '../scripts/research/gpt_social_reader.mjs';

const NOW = Date.parse('2026-10-23T12:00:00Z');
const base = () => ({schema_version:1, generated_at:'2026-10-23T11:00:00Z',
  networks:[{id:'bluesky', source:'bluesky-public-appview', status:'ok', followers:42,
    observed_at:'2026-10-23T10:00:00Z', valid_until:'2026-10-24T11:00:00Z'}]});

for (const observed_at of [undefined, '2026-10-25T00:00:00Z', '2020-01-01T00:00:00Z']) {
  test(`a verified count must have causally plausible observation ${observed_at}`, () => {
    const data = base();
    if (observed_at === undefined) delete data.networks[0].observed_at;
    else data.networks[0].observed_at = observed_at;
    const output = visibleSocialMetrics(data, NOW);
    assert.equal(output.networks[0].followers, null);
    assert.equal(output.totals.coverage, 0);
  });
}
