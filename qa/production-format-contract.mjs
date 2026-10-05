import assert from 'node:assert/strict';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();

async function get(path,opts={}){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(new URL(path,O),{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-production-format-contract/1.0'},
        signal:AbortSignal.timeout(15000),
        ...opts,
      });
      if(r.status!==429&&(r.status<500||r.status>599)) return r;
      last=new Error('transient HTTP '+r.status+' '+path);
    }catch(e){last=e}
    if(i<2) await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  throw last;
}
if(S){
  const r=await get(`/_release/${S}.json?qa_format_release=1`);
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}

const cases=[
  {path:'/sitemap.xml',type:/\b(?:application|text)\/xml\b/i,body:/<(?:urlset|sitemapindex)\b/i},
  {path:'/editoriales-sitemap.xml',type:/\b(?:application|text)\/xml\b/i,body:/<urlset\b/i},
  {path:'/cuaderno/feed.xml',type:/\b(?:application|text)\/(?:rss\+)?xml\b/i,body:/<(?:rss|feed)\b/i},
  {path:'/manifest.json',type:/\b(?:application\/(?:manifest\+)?json|application\/json)\b/i,json:true},
  {path:'/convocatorias-escritores/opportunities.json',type:/\bapplication\/json\b/i,json:true},
  {path:'/convocatorias-escritores/deadlines.ics',type:/\b(?:text\/calendar|application\/octet-stream|text\/plain)\b/i,body:/BEGIN:VCALENDAR/},
  {path:'/service-worker.js',type:/\b(?:application|text)\/(?:javascript|x-javascript)\b/i,body:/\b(?:self\.addEventListener|CACHE_NAMESPACE)\b/},
  {path:'/robots.txt',type:/\btext\/plain\b/i,body:/User-agent:/i},
  {path:'/llms.txt',type:/\btext\/plain\b/i,body:/David Porto/i},
  {path:'/llms-full.txt',type:/\btext\/plain\b/i,body:/David Porto/i},
];

const observations=[];
for(const x of cases){
  const r=await get(x.path+'?qa_format=1');
  const type=(r.headers.get('content-type')||'').toLowerCase();
  const body=await r.text();
  assert.equal(r.status,200,x.path+' status');
  assert.match(type,x.type,x.path+' wrong Content-Type: '+type);
  assert.doesNotMatch(type,/text\/html/,x.path+' served as HTML');
  assert.ok(body.length>10,x.path+' suspiciously empty');
  if(x.json) assert.doesNotThrow(()=>JSON.parse(body),x.path+' invalid JSON');
  if(x.body) assert.match(body,x.body,x.path+' signature mismatch');

  const h=await get(x.path+'?qa_format_head=1',{method:'HEAD'});
  assert.equal(h.status,200,x.path+' HEAD status');
  const headType=(h.headers.get('content-type')||'').toLowerCase();
  assert.match(headType,x.type,x.path+' HEAD Content-Type: '+headType);
  observations.push({path:x.path,type,headType,cache:r.headers.get('cache-control')||''});
}
console.log('PASS production raw-format/MIME contract:',JSON.stringify(observations));
