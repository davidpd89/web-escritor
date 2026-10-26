import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {visibleSocialMetrics} from '../redes-sociales/gpt_social_reader.mjs';

const original = JSON.parse(readFileSync('redes-sociales/social-metrics.json', 'utf8'));
const now = Date.parse(original.generated_at) + 60000;

for (const network of original.networks) {
  test(`${network.id}: reader never exposes untrusted profile URL`, () => {
    const snapshot = structuredClone(original);
    const row = snapshot.networks.find(x => x.id === network.id);
    row.profile_url = 'https://example.org/other-profile';
    const result = visibleSocialMetrics(snapshot, now);
    assert.ok(result.networks.some(x => x.id === network.id),
      `${network.id}: network disappeared`);
    for (const visible of result.networks) {
      assert.equal(Object.hasOwn(visible, 'profile_url'), false,
        `${network.id}: profile_url leaked into public output`);
    }
    assert.equal(JSON.stringify(result).includes('example.org'), false,
      `${network.id}: external destination propagated`);
  });
}