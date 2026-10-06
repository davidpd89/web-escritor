import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { assertProductionRelease } from './production-release-marker.mjs';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const read=p=>fs.readFileSync(p);
const normalizeXml=b=>b.toString('utf8').replace(/\r\n?/g,'\n').trim();

await assertProductionRelease({origin:ORIGIN,sha:SHA,label:'public-artifacts'});

async function get(route,{method='GET'}={}){
  let last;
  for(let attempt=0;attempt<3;attempt++){
    try{
      const u=new URL(route,ORIGIN);
      u.searchParams.set('__qa_artifact',SHA||Date.now().toString(36));
      const r=await fetch(u,{
        method,
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-public-artifacts/1.0'},
        signal:AbortSignal.timeout(20000),
      });
      if(r.status!==429&&(r.status<500||r.status>599)) return r;
      last=new Error(`${route}: transient HTTP ${r.status}`);
    }catch(e){last=e}
    if(attempt<2) await new Promise(r=>setTimeout(r,700*(attempt+1)));
  }
  throw last;
}

async function exact(route,localPath,typeRe){
  const local=read(localPath);
  const r=await get(route);
  assert.equal(r.status,200,`${route}: HTTP ${r.status}`);
  assert.match((r.headers.get('content-type')||'').toLowerCase(),typeRe,`${route}: unexpected Content-Type`);
  const prod=Buffer.from(await r.arrayBuffer());
  assert.deepEqual(prod,local,`${route}: deployed bytes drift from repository`);
  return prod;
}

// RSS is a public API surface for readers and aggregators: prove byte parity,
// item integrity, chronological ordering and that every item still resolves.
const feed=await exact('/cuaderno/feed.xml','cuaderno/feed.xml',/\b(?:application|text)\/(?:rss\+)?xml\b/i);
const feedText=feed.toString('utf8');
assert.match(feedText,/^<\?xml\b/i,'feed: XML declaration missing');
assert.match(feedText,/<rss\b[^>]*version=["']2\.0["']/i,'feed: RSS 2.0 root missing');
assert.match(feedText,/xml-stylesheet[^>]+\/assets\/rss\.xsl/i,'feed: readable XSL link missing');
const items=[...feedText.matchAll(/<item>([\s\S]*?)<\/item>/gi)].map(m=>m[1]);
assert.ok(items.length>=5,`feed: suspiciously few items (${items.length})`);
const decode=s=>String(s||'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
const field=(xml,name)=>decode(xml.match(new RegExp(`<${name}>([\\s\\S]*?)<\\/${name}>`,'i'))?.[1]?.trim()||'');
const guids=[],dates=[];
for(const item of items){
  const guid=field(item,'guid');
  const link=field(item,'link');
  const title=field(item,'title');
  const pubDate=field(item,'pubDate');
  assert.ok(title.length>3,'feed: empty/suspicious item title');
  assert.equal(link,guid,`feed: link/guid drift for ${title}`);
  const u=new URL(link);
  assert.equal(u.origin,ORIGIN,`feed: external item origin for ${title}`);
  assert.ok(u.pathname.startsWith('/cuaderno/'),`feed: non-cuaderno item ${u.pathname}`);
  const ms=Date.parse(pubDate);
  assert.ok(Number.isFinite(ms),`feed: invalid pubDate for ${title}: ${pubDate}`);
  assert.ok(ms<=Date.now()+86400000,`feed: future pubDate for ${title}: ${pubDate}`);
  guids.push(guid);dates.push(ms);
}
assert.equal(new Set(guids).size,guids.length,'feed: duplicate GUIDs');
assert.deepEqual(dates,[...dates].sort((a,b)=>b-a),'feed: items are not newest-first');
for(const url of guids){
  const r=await get(url);
  assert.equal(r.status,200,`feed target failed: ${url} -> ${r.status}`);
}
await exact('/assets/rss.xsl','assets/rss.xsl',/\b(?:application|text)\/(?:xml|xsl)|\btext\/plain\b/i);

// Editorial sitemap is generated independently from sitemap.xml, so keep a
// live parity guard for it as its own public discovery surface.
const editorialMap=await exact('/editoriales-sitemap.xml','editoriales-sitemap.xml',/\b(?:application|text)\/xml\b/i);
const editorialText=normalizeXml(editorialMap);
const locs=[...editorialText.matchAll(/<loc>(.*?)<\/loc>/gis)].map(m=>m[1].trim());
assert.ok(locs.length>=100,`editoriales sitemap: suspiciously few URLs (${locs.length})`);
assert.equal(new Set(locs).size,locs.length,'editoriales sitemap: duplicate <loc>');
for(const loc of locs){
  const u=new URL(loc);
  assert.equal(u.origin,ORIGIN,'editoriales sitemap: external origin');
  assert.ok(
    u.pathname==='/metodologia-editorial/'||u.pathname==='/editoriales/'||u.pathname.startsWith('/editoriales/'),
    'editoriales sitemap: unexpected route outside editorial resource surfaces'
  );
}

// Event calendar files are easy to orphan because they are generated from
// JSON-LD and linked separately. Compare every tracked .ics byte-for-byte.
const eventDir='assets/events/calendar';
const localIcs=fs.existsSync(eventDir)
  ? fs.readdirSync(eventDir).filter(x=>x.endsWith('.ics')).sort()
  : [];
const eventos=fs.readFileSync('eventos.html','utf8');
const linked=[...eventos.matchAll(/href=["']\/assets\/events\/calendar\/([^"'?#]+\.ics)["'][^>]*data-calendar-download/gi)]
  .map(m=>m[1]).sort();
assert.deepEqual(linked,localIcs,'eventos: visible calendar links differ from tracked ICS files');
for(const name of localIcs){
  const route=`/assets/events/calendar/${encodeURIComponent(name)}`;
  const bytes=await exact(route,path.join(eventDir,name),/\b(?:text\/calendar|application\/octet-stream|text\/plain)\b/i);
  const text=bytes.toString('utf8');
  assert.match(text,/BEGIN:VCALENDAR\r?\n/,`${name}: VCALENDAR missing`);
  assert.match(text,/BEGIN:VEVENT\r?\n/,`${name}: VEVENT missing`);
  assert.match(text,/UID:[^\r\n]+/,`${name}: UID missing`);
  assert.match(text,/DTSTART[^:]*:[^\r\n]+/,`${name}: DTSTART missing`);
}

console.log(`PASS production public artifacts: RSS ${items.length} items; editoriales sitemap ${locs.length} URLs; event calendars ${localIcs.length}`);
