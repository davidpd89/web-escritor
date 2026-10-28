import test from 'node:test';
import assert from 'node:assert/strict';
import {visibleSocialMetrics} from '../scripts/research/gpt_social_reader.mjs';
const NOW = Date.parse('2026-10-22T12:00:00Z');
function fixture() {
  return {schema_version: 1, generated_at: '2026-10-22T11:00:00Z',
    networks: [
      {id:'bluesky', followers: 9, source:'bluesky-public-appview', status:'ok', observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-23T11:00:00Z'},
      {id:'threads', followers: 0, source:'metricool-mcp-export', status:'ok', observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-24T11:00:00Z'}
    ], totals: {follower_relationships: 999999, coverage: 99, eligible:99}
  };
}
test('recomputes totals instead of trusting stale or forged aggregate', () => {
  const out=visibleSocialMetrics(fixture(), NOW);
  assert.deepEqual(out.totals, {follower_relationships: 9, coverage:2,eligible:6});
});
test('zero followers is a genuine count', () => {
  const out=visibleSocialMetrics(fixture(),NOW);
  assert.equal(out.networks[2].followers, 0);
});
test('expires per-network counters even if cached status claims ok', () => {
  const out=visibleSocialMetrics(fixture(), Date.parse('2026-10-23T11:00:01Z'));
  assert.equal(out.networks[0].followers,null);
  assert.equal(out.totals.follower_relationships,0);
  assert.equal(out.totals.coverage,1);
});
test('after all deadlines, no fake zero',()=>{
  const out=visibleSocialMetrics(fixture(),Date.parse('2026-10-25T00:00:00Z'));
  assert.equal(out.totals.follower_relationships,null);
  assert.equal(out.totals.coverage,0);
});
test('at exact expiration boundary number is still valid',()=>{
  assert.equal(visibleSocialMetrics(fixture(),Date.parse('2026-10-23T11:00:00Z')).totals.coverage,2);
});
test('missing deadlines fail closed',()=>{
  const x=fixture(); delete x.networks[0].valid_until;
  assert.equal(visibleSocialMetrics(x,NOW).networks[0].followers,null);
});
test('wrong provider cannot claim a counter',()=>{
  const x=fixture(); x.networks[0].source='metricool-mcp-export';
  assert.equal(visibleSocialMetrics(x,NOW).totals.follower_relationships,0);
});
test('duplicated account rejects entire corrupted snapshot',()=>{
  const x=fixture(); x.networks.push({...x.networks[0]});
  assert.equal(visibleSocialMetrics(x,NOW).totals.coverage,0);
});
test('unknown network in snapshot rejected, not published',()=>{
  const x=fixture();x.networks.push({id:'x',followers:888,observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-24T11:00:00Z'});
  assert.equal(visibleSocialMetrics(x,NOW).totals.coverage,0);
});
test('future-generated snapshot yields no counters',()=>{
  const x=fixture();x.generated_at='2026-10-23T11:00:00Z';
  assert.equal(visibleSocialMetrics(x,NOW).totals.coverage,0);
});
test('invalid input yields no counters',()=>{
  for(const x of [null,[],true,{schema_version:2,networks:[]},{}])
    assert.equal(visibleSocialMetrics(x,NOW).totals.follower_relationships,null);
});
test('only safe integer counters are accepted',()=>{
  for(const value of [true,-1,'99',1.2,Number.MAX_SAFE_INTEGER+1]){
    const x=fixture();x.networks[0].followers=value;
    assert.equal(visibleSocialMetrics(x,NOW).networks[0].followers,null);
  }
});
test('no untrusted external URL is emitted',()=>{
  const x=fixture();x.networks[0].profile_url='https://attacker.example/path';
  assert.ok(!JSON.stringify(visibleSocialMetrics(x,NOW)).includes('attacker.example'));
});

test('browser accepts verified Instagram, TikTok and Pinterest from Metricool', () => {
  const x=fixture();
  for (const [id, followers] of [['instagram',21],['tiktok',22],['pinterest',23]]) {
    x.networks.push({id, followers, source:'metricool-mcp-export',status:'ok',
                     observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-24T11:00:00Z'});
  }
  const output=visibleSocialMetrics(x,NOW);
  assert.deepEqual(output.totals,{follower_relationships:75,coverage:5,eligible:6});
  assert.deepEqual(output.networks.map(x=>x.id),
    ['bluesky','mastodon','threads','instagram','tiktok','pinterest']);
});
test('browser rejects wrong metricool source for one of the new networks', () => {
  const x=fixture();
  x.networks.push({id:'pinterest',followers:50,source:'bluesky-public-appview',
                   status:'ok',observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-24T11:00:00Z'});
  const output=visibleSocialMetrics(x,NOW);
  assert.equal(output.totals.follower_relationships,9);
  assert.equal(output.totals.coverage,2);
});
test('a new verified network also expires while the last-good JSON stays cached', () => {
  const x=fixture();
  x.networks.push({id:'instagram',followers:41,source:'metricool-mcp-export',
                   status:'ok',observed_at:'2026-10-22T10:00:00Z',valid_until:'2026-10-22T12:00:01Z'});
  const output=visibleSocialMetrics(x,NOW+2000);
  assert.equal(output.totals.follower_relationships,9);
  assert.equal(output.totals.coverage,2);
});

test('impossibly distant valid_until never defeats 48-hour TTL', () => {
  const x=fixture(); x.networks[0].valid_until='2099-01-01T00:00:00Z';
  const visible=visibleSocialMetrics(x,NOW);
  assert.equal(visible.networks[0].followers,null);
  assert.equal(visible.totals.follower_relationships,0);
});
test('cached JSON older than 48h never accepts impossible future deadlines', () => {
  const x=fixture(); x.networks[0].valid_until='2099-01-01T00:00:00Z';
  x.networks[1].valid_until='2099-01-01T00:00:00Z';
  const visible=visibleSocialMetrics(x,Date.parse('2026-10-26T10:00:00Z'));
  assert.equal(visible.totals.follower_relationships,null);
  assert.equal(visible.totals.coverage,0);
});
test('safe per-network integer values must not yield an imprecise total', () => {
  const x=fixture();
  x.networks[0].followers=Number.MAX_SAFE_INTEGER;
  x.networks[1].followers=12;
  const visible=visibleSocialMetrics(x,NOW);
  assert.equal(visible.totals.coverage,2);
  assert.equal(visible.totals.follower_relationships,null);
});
