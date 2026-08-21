import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';

const BASE=process.env.BASE_SHA;assert(BASE,'BASE_SHA requerido');
const paths=['empieza-aqui/index.html','mapa-del-sitio/index.html','404.html'];
const outDir=process.env.QA_OUT||'qa-artifacts';fs.mkdirSync(outDir,{recursive:true});
const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
const one=(html,re)=>(html.match(re)||[])[1]||'';
const captures=(html,re)=>[...html.matchAll(re)].map(m=>m[1]);
const tags=(html,re)=>[...html.matchAll(re)].map(m=>m[0]);
const attr=(tag,name)=>one(tag,new RegExp(`${name}\\s*=\\s*["']([^"']*)["']`,'i'));
function inventory(html){
  const metaTags=tags(html,/<meta\b[^>]*>/gi),linkTags=tags(html,/<link\b[^>]*>/gi),scriptTags=tags(html,/<script\b[^>]*>[\s\S]*?<\/script>/gi);
  const hrefs=captures(html,/<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>/gi);
  const sectionTags=tags(html,/<section\b[^>]*>/gi);
  return {
    title:strip(one(html,/<title>([\s\S]*?)<\/title>/i)),
    description:attr(metaTags.find(t=>/name\s*=\s*["']description["']/i.test(t))||'','content'),
    robots:attr(metaTags.find(t=>/name\s*=\s*["']robots["']/i.test(t))||'','content'),
    canonical:attr(linkTags.find(t=>/rel\s*=\s*["']canonical["']/i.test(t))||'','href'),
    h1:captures(html,/<h1\b[^>]*>([\s\S]*?)<\/h1>/gi).map(strip),h2:captures(html,/<h2\b[^>]*>([\s\S]*?)<\/h2>/gi).map(strip),h3:captures(html,/<h3\b[^>]*>([\s\S]*?)<\/h3>/gi).map(strip),
    hrefs:[...new Set(hrefs)],
    ariaCurrent:tags(html,/<[^>]+aria-current\s*=\s*["']page["'][^>]*>/gi).map(t=>({tag:t,href:attr(t,'href')})),
    jsonLd:scriptTags.filter(s=>/application\/ld\+json/i.test(s)).map(strip),
    scripts:captures(html,/<script\b[^>]*src\s*=\s*["']([^"']+)["'][^>]*>/gi),
    stylesheets:linkTags.filter(t=>/rel\s*=\s*["']stylesheet["']/i.test(t)).map(t=>attr(t,'href')).filter(Boolean),
    localAssets:[...new Set(captures(html,/(?:src|href)\s*=\s*["'](\/assets\/[^"']+)["']/gi))],
    sections:sectionTags.map(t=>attr(t,'id')||'(sin id)')
  };
}
const baseText=p=>execFileSync('git',['show',`${BASE}:${p}`],{encoding:'utf8'});
const report={baseSha:BASE,pages:{}};
for(const p of paths){
  const before=inventory(baseText(p)),after=inventory(fs.readFileSync(p,'utf8'));
  const removed=before.hrefs.filter(x=>!after.hrefs.includes(x)),added=after.hrefs.filter(x=>!before.hrefs.includes(x));
  assert.deepEqual(removed,[],`${p}: destinos eliminados sin preservar: ${removed.join(', ')}`);
  report.pages[p]={before,after,addedDestinations:added,removedDestinations:removed,metadataChanges:{title:before.title===after.title?null:[before.title,after.title],description:before.description===after.description?null:[before.description,after.description],robots:before.robots===after.robots?null:[before.robots,after.robots],canonical:before.canonical===after.canonical?null:[before.canonical,after.canonical]}};
}
fs.writeFileSync(`${outDir}/findability-inventory.json`,JSON.stringify(report,null,2));
console.log('FINDABILITY INVENTORY/PRESERVATION: OK');
