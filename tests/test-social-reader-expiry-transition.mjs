import test from 'node:test';
import assert from 'node:assert/strict';
import {visibleSocialMetrics} from '../scripts/research/gpt_social_reader.mjs';

const generated = '2026-10-23T11:00:00Z';
const expiry = Date.parse('2026-10-24T10:00:00Z');
const snapshot = {
  schema_version: 1,
  generated_at: generated,
  networks: [
    {id:'bluesky', source:'bluesky-public-appview', status:'ok', followers:42,
     observed_at:'2026-10-23T10:00:00Z', valid_until:'2026-10-24T10:00:00Z'},
    {id:'mastodon', source:'mastodon-public-search', status:'ok', followers:80,
     observed_at:'2026-10-23T10:00:00Z', valid_until:'2026-10-24T11:00:00Z'}
  ]
};

for (const [label, now, expectedBluesky, expectedTotal, coverage] of [
  ['before', expiry - 1, 42, 122, 2],
  ['at', expiry, 42, 122, 2],
  ['after', expiry + 1, null, 80, 1]
]) {
  test(`social expiry ${label} preserves only valid claims`, () => {
    const output = visibleSocialMetrics(snapshot, now);
    const bluesky = output.networks.find(row => row.id === 'bluesky');
    const mastodon = output.networks.find(row => row.id === 'mastodon');
    assert.equal(bluesky.followers, expectedBluesky, `bluesky ${label}: caducidad incorrecta`);
    assert.equal(mastodon.followers, 80, `mastodon ${label}: dato vigente descartado`);
    assert.equal(output.totals.follower_relationships, expectedTotal, `total ${label}: incluye cifra caducada`);
    assert.equal(output.totals.coverage, coverage, `coverage ${label}: redes válidas incorrectas`);
  });
}
