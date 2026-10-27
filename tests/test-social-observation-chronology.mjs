import test from 'node:test';
import assert from 'node:assert/strict';
import {visibleSocialMetrics} from '../redes-sociales/gpt_social_reader.mjs';

const NOW=Date.parse('2026-10-24T08:30:00Z');
const IDS=['bluesky','mastodon','threads','instagram','tiktok','pinterest'];
const SOURCE=id=>id==='bluesky'?'bluesky-public-appview':id==='mastodon'?'mastodon-public-search':'metricool-mcp-export';
function snapshot(id,observed_at){
  return {schema_version:1,generated_at:'2026-10-24T08:00:00Z',networks:[{id,source:SOURCE(id),followers:124,status:'ok',observed_at,valid_until:'2026-10-25T08:00:00Z'}]};
}
const invalid=[
  ['future observation','2026-10-25T07:00:00Z'],
  ['after generation','2026-10-24T08:10:00Z'],
  ['invalid day','2026-02-30'],
  ['invalid leap date','2025-02-29'],
  ['invalid month','2026-13-10'],
  ['missing observation',null]
];
for(const id of IDS){
  for(const [label,observed] of invalid){
    test(`${id}: ${label} must fail closed`,()=>{
      const output=visibleSocialMetrics(snapshot(id,observed),NOW);
      const card=output.networks.find(row=>row.id===id);
      assert.equal(card.followers,null,`${id}: ${label} must not advertise current followers`);
      assert.equal(output.totals.coverage,0);
      assert.equal(output.totals.follower_relationships,null);
    });
  }
}
for(const id of IDS){
  test(`${id}: an observation at generation time is accepted`,()=>{
    const result=visibleSocialMetrics(snapshot(id,'2026-10-24T08:00:00Z'),NOW);
    assert.equal(result.networks.find(row=>row.id===id).followers,124);
  });
}
