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

// A baseline destination may only disappear if it was already broken: the
// target file does not exist, or its #anchor matches no id in that file.
// Anything still reachable must be preserved, so this stays a real guard
// against silently dropping working links.
function brokenInBaseline(href){
  if(!href.startsWith('/')||href.startsWith('//'))return null;
  const [rawPath,hash]=href.split('#');
  let target=(rawPath||'/').replace(/^\//,'');
  if(target===''||target.endsWith('/'))target+='index.html';
  if(!fs.existsSync(target))return `fichero inexistente: ${target}`;
  if(!hash)return null;
  const html=fs.readFileSync(target,'utf8');
  const hasId=new RegExp(`\\bid\\s*=\\s*["']${hash.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}["']`,'i').test(html);
  return hasId?null:`anchor inexistente: #${hash} en ${target}`;
}

const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const mainWithId=(html,id)=>new RegExp(`<main\\b[^>]*\\bid\\s*=\\s*["']${esc(id)}["']`,'i').test(html);
function skipTarget(html){
  const m=html.match(/<a\b[^>]*class\s*=\s*["'][^"']*skip-link[^"']*["'][^>]*href\s*=\s*["']#([^"']+)["']/i)
        ||html.match(/<a\b[^>]*href\s*=\s*["']#([^"']+)["'][^>]*class\s*=\s*["'][^"']*skip-link/i);
  return m?m[1]:null;
}

// The one same-page case that is a rename rather than a removal: the fragment
// named this page's <main> landmark, and the page still exposes that landmark
// under a new id with its skip link resolving to it. Deliberately narrow — it
// checks that the destination is still <main> and still reachable from the
// skip link, so a page that simply dropped its skip link, or points it at
// something that is not the landmark, still fails. That the target is also
// focusable is asserted separately by scripts/check-heading-structure.py.
function landmarkRenamed(href,beforeHtml,afterHtml){
  if(!href.startsWith('#'))return null;
  const id=href.slice(1);
  if(!mainWithId(beforeHtml,id))return null;
  const now=skipTarget(afterHtml);
  if(!now||!mainWithId(afterHtml,now))return null;
  return `landmark <main> renombrado: #${id} -> #${now}`;
}

// An unresolvable BASE_SHA would make every page look new and pass the gate
// in vacuum, so the ref is verified before anything else.
try{execFileSync('git',['rev-parse','--verify',`${BASE}^{commit}`],{stdio:'ignore'});}
catch{throw new Error(`BASE_SHA no resuelve a un commit: ${BASE}`);}
const existsInBase=p=>{
  try{execFileSync('git',['cat-file','-e',`${BASE}:${p}`],{stdio:'ignore'});return true;}
  catch{return false;}
};

const report={baseSha:BASE,pages:{},introduced:[]};
for(const p of paths){
  // A page that did not exist in the base has no destinations to preserve.
  // Narrow on purpose: it only covers "new in this branch", so deleting a page
  // still fails on readFileSync below.
  if(!existsInBase(p)){report.introduced.push(p);continue;}
  const beforeHtml=baseText(p),afterHtml=fs.readFileSync(p,'utf8');
  const before=inventory(beforeHtml),after=inventory(afterHtml);
  const removed=before.hrefs.filter(x=>!after.hrefs.includes(x)),added=after.hrefs.filter(x=>!before.hrefs.includes(x));
  const removedJustification=Object.fromEntries(removed.map(h=>[h,brokenInBaseline(h)||landmarkRenamed(h,beforeHtml,afterHtml)]));
  const unjustified=removed.filter(h=>!removedJustification[h]);
  assert.deepEqual(unjustified,[],`${p}: destinos eliminados sin preservar: ${unjustified.join(', ')}`);
  report.pages[p]={before,after,addedDestinations:added,removedDestinations:removed,removedJustification,metadataChanges:{title:before.title===after.title?null:[before.title,after.title],description:before.description===after.description?null:[before.description,after.description],robots:before.robots===after.robots?null:[before.robots,after.robots],canonical:before.canonical===after.canonical?null:[before.canonical,after.canonical]}};
}
fs.writeFileSync(`${outDir}/findability-inventory.json`,JSON.stringify(report,null,2));
if(report.introduced.length)console.log(`FINDABILITY INVENTORY: ${report.introduced.length} página(s) nuevas respecto a la base, sin destinos que preservar: ${report.introduced.join(', ')}`);
console.log('FINDABILITY INVENTORY/PRESERVATION: OK');
