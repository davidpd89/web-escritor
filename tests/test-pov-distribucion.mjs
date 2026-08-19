import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const api = require('../assets/pov-distribucion-engine.js');
function ok(cond,msg){ if(!cond) throw new Error(msg); }
const input=['1.1 | Ana | 1000','1.2 | Ana | 500','2.1 | Bruno | 1000','2.2 | Ana | 1500','3.1 | Bruno | 1000'].join('\n');
const parsed=api.parse(input); ok(parsed.errors.length===0,'parse errors');
const a=api.analyze(parsed.scenes); ok(a.totalScenes===5,'scene count'); ok(a.totalPovs===2,'pov count'); ok(a.totalWords===5000,'word total');
const ana=a.povs.find(x=>x.pov==='Ana'); const bruno=a.povs.find(x=>x.pov==='Bruno');
ok(ana.sceneCount===3,'Ana scenes'); ok(ana.longestRun===2,'Ana run'); ok(ana.maxInternalGap===1,'Ana gap'); ok(Math.abs(ana.wordShare-.6)<1e-9,'Ana word share');
ok(bruno.sceneCount===2,'Bruno scenes'); ok(bruno.maxInternalGap===1,'Bruno gap');
const partial=api.parse('A | Ana\nB | Bruno | 200'); ok(partial.errors.length===0,'optional words'); ok(api.analyze(partial.scenes).completeWords===false,'partial words must disable word shares');
ok(api.parse('A | Ana | hola').errors.length===1,'invalid words');
ok(api.parse('A | Ana | 10 | extra').errors.length===1,'extra column');
console.log('tests/test-pov-distribucion: OK');
