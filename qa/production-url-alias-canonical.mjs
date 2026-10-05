import assert from 'node:assert/strict';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ALIASES=[
  ['/index.html','/'],
  ['/editoriales/index.html','/editoriales/'],
  ['/convocatorias-escritores/index.html','/convocatorias-escritores/'],
  ['/metodologia-editorial/index.html','/metodologia-editorial/'],
  ['/cuaderno/index.html','/cuaderno/'],
  ['/herramientas/index.html','/herramientas/'],
  ['/mapa-del-sitio/index.html','/mapa-del-sitio/'],
];

await assertProductionRelease({origin:O,sha:S,label:'url-alias-canonical'});

const attr=(tag,name)=>{
  const re=new RegExp('\\b'+name.replace(':','\\:')+'\\s*=\\s*(["\\\'])(.*?)\\1','i');
  return tag.match(re)?.[2]||'';
};
const tags=(html,name)=>html.match(new RegExp('<'+name+'\\b[^>]*>','gi'))||[];
const canonical=html=>{
  for(const tag of tags(html,'link')){
    if(attr(tag,'rel').toLowerCase().split(/\s+/).includes('canonical')) return attr(tag,'href');
  }
  return '';
};
const ogUrl=html=>{
  for(const tag of tags(html,'meta')){
    if(attr(tag,'property').toLowerCase()==='og:url') return attr(tag,'content');
  }
  return '';
};

async function get(url){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(url,{redirect:'follow',headers:{'cache-control':'no-cache','user-agent':'david-porto-url-alias-audit/1.0'},signal:AbortSignal.timeout(15000)});
      const body=await r.text();
      if(r.status!==429&&(r.status<500||r.status>599)) return {r,body};
      last=new Error('transient HTTP '+r.status+' '+url);
    }catch(e){last=e}
    if(i<2) await new Promise(resolve=>setTimeout(resolve,700*(i+1)));
  }
  throw last;
}

for(const [alias,preferred] of ALIASES){
  const {r,body}=await get(O+alias+'?qa_alias=1');
  assert.equal(r.status,200,alias+': HTTP '+r.status);
  const final=new URL(r.url);
  assert.equal(final.origin,O,alias+': redirected off canonical origin');
  assert.ok(final.pathname===alias||final.pathname===preferred,alias+': unexpected final path '+final.pathname);
  const expected=new URL(preferred,O).href;
  const canon=canonical(body);
  assert.equal(canon,expected,alias+': canonical '+canon+' != '+expected);
  const og=ogUrl(body);
  if(og) assert.equal(og,expected,alias+': og:url '+og+' != '+expected);
}

const sitemap=(await get(O+'/sitemap.xml?qa_alias=1')).body;
assert.doesNotMatch(sitemap,/\/index\.html<\/loc>/i,'sitemap must not expose index.html aliases');
console.log('PASS production URL aliases: '+ALIASES.length+' index.html aliases converge semantically on canonical URLs');
