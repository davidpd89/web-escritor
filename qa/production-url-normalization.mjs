import assert from 'node:assert/strict';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const canonical=new URL(O);

await assertProductionRelease({origin:O,sha:S,label:'url-normalization'});

async function fetchTimeout(url,opts={}){
  return fetch(url,{...opts,signal:AbortSignal.timeout(15000),headers:{'cache-control':'no-cache','user-agent':'david-porto-url-normalization/1.0',...(opts.headers||{})}});
}

// HTTP must end on the HTTPS canonical origin.
{
  const http=new URL(canonical.href);http.protocol='http:';
  const r=await fetchTimeout(http,{redirect:'follow'});
  assert.equal(r.status,200,`HTTP entry final status ${r.status}`);
  const final=new URL(r.url);
  assert.equal(final.protocol,'https:','HTTP entry did not upgrade to HTTPS');
  assert.equal(final.host,canonical.host,'HTTP entry changed canonical host');
}

// Directory routes must normalize the missing trailing slash and preserve the query.
for(const route of ['/editoriales/','/convocatorias-escritores/','/metodologia-editorial/','/cuaderno/','/herramientas/','/mapa-del-sitio/']){
  const noSlash=route.slice(0,-1);
  const r=await fetchTimeout(`${O}${noSlash}?qa_norm=1`,{redirect:'follow'});
  assert.equal(r.status,200,`${noSlash}: final HTTP ${r.status}`);
  const final=new URL(r.url);
  assert.equal(final.origin,canonical.origin,`${noSlash}: canonical origin drift`);
  assert.equal(final.pathname,route,`${noSlash}: did not normalize to ${route}; got ${final.pathname}`);
  assert.equal(final.searchParams.get('qa_norm'),'1',`${noSlash}: redirect dropped query string`);
}

// Canonical routes themselves must not bounce to another host/path.
for(const route of ['/','/prensa.html','/autor.html','/editoriales/','/convocatorias-escritores/']){
  const r=await fetchTimeout(`${O}${route}?qa_direct=1`,{redirect:'follow'});
  assert.equal(r.status,200,`${route}: HTTP ${r.status}`);
  const final=new URL(r.url);
  assert.equal(final.origin,canonical.origin,`${route}: origin drift`);
  assert.equal(final.pathname,route,`${route}: unexpected path redirect to ${final.pathname}`);
}

// www is DNS/hosting-owned. Observe it without making repo CI depend on external DNS configuration.
try{
  const www=new URL(canonical.href);www.hostname=`www.${canonical.hostname}`;
  const r=await fetchTimeout(www,{redirect:'follow'});
  const final=new URL(r.url);
  console.log(`WWW observation: ${r.status} ${www.href} -> ${final.href}`);
}catch(error){
  console.log(`WWW observation: unavailable (${error?.message||error})`);
}

console.log('PASS production URL normalization: HTTPS + canonical origin + directory slash/query preservation');
