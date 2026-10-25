#!/usr/bin/env node
// Advisory-only QA scope planner. Never authorizes skipping required checks.
import { execFileSync } from 'node:child_process';
import { appendFileSync } from 'node:fs';

export function planShadow(files) {
  const all = ['sitewide-reflow', 'pa11y-baseline', 'lighthouse', 'content-indexes', 'tool-tests'];
  const names = files.map(x => typeof x === 'string' ? {status:'M',path:x} : x);
  if (!names.length) return {mode:'full',checks:all,routes:[],reason:'No diff evidence'};
  const invalid = names.some(x => !x || typeof x.path !== 'string' || !x.path || !/^[A-Z]$/.test(x.status || '') || !x.path.startsWith('./') && x.path.includes('..') );
  if (invalid) return {mode:'full',checks:all,routes:[],reason:'Incomplete or unsafe diff evidence'};
  if (names.some(x => x.status !== 'M' && x.status !== 'A')) return {mode:'full',checks:all,routes:[],reason:'Deletion, rename, copy or unknown change'};
  const isDoc = p => /^(?:docs\/|\.ci\/)/.test(p) || /(?:^|\/)[^/]+\.md$/i.test(p) || ['.gitignore','.gitattributes'].includes(p);
  const isOwn = p => ['scripts/qa-gate-shadow.mjs','qa/qa-gate-shadow.test.mjs','.github/workflows/qa-gate-shadow.yml'].includes(p);
  const html = names.filter(x => x.path.endsWith('.html') && !x.path.startsWith('scripts/') && !x.path.startsWith('tests/') && !x.path.startsWith('qa/'));
  const unknown = names.filter(x => !isDoc(x.path) && !isOwn(x.path) && !html.includes(x));
  if (unknown.length) return {mode:'full',checks:all,routes:[],reason:'Shared code, generated data, tooling or unclassified path'};
  if (!html.length) return {mode:'minimal',checks:['unit-and-static'],routes:[],reason:'Only documentation or shadow gate itself'};
  if (html.length > 40) return {mode:'full',checks:all,routes:[],reason:'More than 40 HTML pages changed'};
  const routes = [...new Set(['/', ...html.map(x => {
    const p = '/' + x.path.replace(/^\.\//,'').replace(/\/index\.html$/i,'/');
    return p === '/index.html' ? '/' : p;
  })])].sort();
  return {mode:'targeted',checks:['unit-and-static','targeted-reflow','targeted-pa11y','content-indexes'],routes,reason:'Only public HTML pages and safe metadata changed'};
}

function changedFiles(base, head) {
  if (!base || !head || !/^[a-f0-9]{40}$/i.test(base) || !/^[a-f0-9]{40}$/i.test(head)) throw Error('Unknown base/head SHA');
  const out=execFileSync('git',['diff','--no-renames','--name-status',base,head],{encoding:'utf8',maxBuffer:10*1024*1024});
  return out.split(/\r?\n/).filter(Boolean).map(line => {
    const match = line.match(/^([A-Z])[0-9]*\t(.+)$/);
    if (!match) throw Error('Unrecognized git diff status');
    return {status:match[1],path:match[2]};
  });
}
if (process.argv[1]?.replace(/\\/g,'/').endsWith('/qa-gate-shadow.mjs')) {
  const base=process.env.BASE_SHA, head=process.env.HEAD_SHA;
  let decision;
  try { decision=planShadow(changedFiles(base,head)); }
  catch(e) { decision={mode:'full',checks:['sitewide-reflow','pa11y-baseline','lighthouse','content-indexes','tool-tests'],routes:[],reason:'Fail-closed: '+String(e.message).slice(0,150)}; }
  const report=['### QA gate (shadow only)','This advisory report does not suppress or replace any existing check.','', 'Mode: **'+decision.mode+'**','Reason: '+decision.reason,'Suggested checks: '+decision.checks.join(', '),'Routes: '+(decision.routes.join(', ') || 'not applicable'),''].join('\n');
  process.stdout.write(report+'\n');
  if(process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY,report+'\n');
}
