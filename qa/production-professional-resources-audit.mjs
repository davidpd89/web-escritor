import assert from 'node:assert/strict';
import fs from 'node:fs';

const ROOT=process.cwd();
const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim().toLowerCase();
const TODAY=new Date().toISOString().slice(0,10);
const read=p=>fs.readFileSync(p,'utf8');
const json=p=>JSON.parse(read(p));
const norm=s=>String(s||'').replace(/\r\n?/g,'\n').trim();
const text=s=>norm(String(s||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' '));
const title=h=>text(h.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]);
const h1=h=>text(h.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)?.[1]);
const canonical=h=>[...(h.match(/<link\b[^>]*>/gi)||[])].find(x=>/rel=["'][^"']*canonical/i.test(x))?.match(/href=["']([^"']+)/i)?.[1]||'';
const locs=x=>[...x.matchAll(/<loc>(.*?)<\/loc>/gis)].map(m=>m[1].trim());
const days=(a,b)=>(Date.parse(a+'T00:00:00Z')-Date.parse(b+'T00:00:00Z'))/86400000;

async function get(route){
  const u=new URL(route,ORIGIN);u.searchParams.set('__qa',SHA||TODAY);
  const r=await fetch(u,{redirect:'follow',headers:{'cache-control':'no-cache','user-agent':'david-porto-postdeploy-audit/1.0'},signal:AbortSignal.timeout(15000)});
  return {status:r.status,body:await r.text(),url:r.url,headers:r.headers};
}
async function retry(route){let last,e;for(let i=0;i<4;i++){try{last=await get(route);if(last.status!==429&&(last.status<500||last.status>599))return last;e=null}catch(x){e=x}if(i<3)await new Promise(r=>setTimeout(r,800*(i+1)))}if(last)return last;throw e}
async function exact(route,file,isJson=false){const r=await retry(route);assert.equal(r.status,200,route);if(isJson)assert.deepEqual(JSON.parse(r.body),json(file),route);else assert.equal(norm(r.body),norm(read(file)),route);return r}
async function pool(xs,n,fn){let i=0;await Promise.all(Array.from({length:n},async()=>{while(i<xs.length){const x=xs[i++];await fn(x)}}))}

if(SHA){const r=await retry(`/_release/${SHA}.json`);assert.equal(r.status,200);assert.deepEqual(JSON.parse(r.body),{schemaVersion:1,sha:SHA})}

const ed=JSON.parse((await exact('/editoriales/editoriales-data.json','editoriales/editoriales-data.json',true)).body);
assert.ok(ed.publishers.length>=100,`editorial corpus too small: ${ed.publishers.length}`);
const radar=JSON.parse((await exact('/convocatorias-escritores/opportunities.json','convocatorias-escritores/opportunities.json',true)).body);
assert.ok(radar.generated_for<=TODAY && days(TODAY,radar.generated_for)<=1,`stale generated_for ${radar.generated_for}`);
for(const x of radar.items){assert.ok(x.deadline>=TODAY,`${x.id}: expired ${x.deadline}`);assert.ok(x.verified_at<=TODAY&&days(TODAY,x.verified_at)<=30,`${x.id}: stale verification`)}
for(const x of radar.watchlist||[])assert.ok(x.verified_at<=TODAY&&days(TODAY,x.verified_at)<=30,`${x.id}: stale watch`);
const ics=(await exact('/convocatorias-escritores/deadlines.ics','convocatorias-escritores/deadlines.ics')).body.replace(/\r\n/g,'\n');
assert.equal((ics.match(/BEGIN:VEVENT/g)||[]).length,radar.items.length,'ICS count');
for(const x of radar.items){assert.ok(ics.includes(`UID:${x.id}@davidportodiaz.com`),`ICS UID ${x.id}`);assert.ok(ics.includes(`DTSTART;VALUE=DATE:${x.deadline.replaceAll('-','')}`),`ICS date ${x.id}`)}

const reg=json('data/content-registry.json'),defs=reg.defaults||{};
const routes=reg.entries.map(x=>({...defs,...x})).filter(x=>x.status==='public'&&/^(editoriales\/|convocatorias-escritores\/|metodologia-editorial\/)/.test(x.sourceFile||'')&&(x.sourceFile||'').endsWith('.html'));
const failures=[];
await pool(routes,10,async x=>{try{const r=await retry(x.url);assert.equal(r.status,200,x.url);const local=read(x.sourceFile);assert.equal(title(r.body),title(local),`${x.url} title`);assert.equal(canonical(r.body),canonical(local),`${x.url} canonical`);assert.equal(h1(r.body),h1(local),`${x.url} h1`);assert.match(r.body,/<html\b[^>]*lang=["']es["']/i,`${x.url} lang`);assert.doesNotMatch(r.body,/name=["']robots["'][^>]*content=["'][^"']*noindex/i,`${x.url} noindex`)}catch(e){failures.push(e.message)}});
assert.deepEqual(failures,[],failures.join('\n'));

const es=await retry('/editoriales-sitemap.xml');assert.equal(es.status,200);assert.deepEqual(locs(es.body),locs(read('editoriales-sitemap.xml')),'editorial sitemap');
const sm=await retry('/sitemap.xml');assert.equal(sm.status,200);const all=locs(sm.body);assert.equal(new Set(all).size,all.length,'duplicate sitemap URLs');for(const x of routes)assert.ok(all.includes(new URL(x.url,ORIGIN).href),`sitemap missing ${x.url}`);
await exact('/llms.txt','llms.txt');await exact('/llms-full.txt','llms-full.txt');
for(const p of ['/editoriales','/convocatorias-escritores','/metodologia-editorial']){const r=await retry(p);assert.equal(r.status,200);assert.equal(new URL(r.url).pathname,p+'/')}
const miss=await retry('/editoriales/__qa-missing__/');assert.equal(miss.status,404,'missing editorial must 404');
console.log(`PASS production parity: ${ed.publishers.length} editorials, ${radar.items.length} opportunities, ${routes.length} professional routes`);
