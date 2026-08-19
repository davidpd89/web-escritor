import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const api = require('../assets/pov-distribucion-engine.js');
function ok(cond,msg){ if(!cond) throw new Error(msg); }
const input=['1.1 | Noa | 1000','1.2 | Noa | 500','2.1 | Brais | 1000','2.2 | Noa | 1500','3.1 | Brais | 1000'].join('\n');
const parsed=api.parse(input); ok(parsed.errors.length===0,'parse errors');
const a=api.analyze(parsed.scenes); ok(a.totalScenes===5,'scene count'); ok(a.totalPovs===2,'pov count'); ok(a.totalWords===5000,'word total');
const noa=a.povs.find(x=>x.pov==='Noa'); const brais=a.povs.find(x=>x.pov==='Brais');
ok(noa.sceneCount===3,'Noa scenes'); ok(noa.longestRun===2,'Noa run'); ok(noa.maxInternalGap===1,'Noa gap'); ok(Math.abs(noa.wordShare-.6)<1e-9,'Noa word share');
ok(brais.sceneCount===2,'Brais scenes'); ok(brais.maxInternalGap===1,'Brais gap');
const partial=api.parse('A | Noa\nB | Brais | 200'); ok(partial.errors.length===0,'optional words'); ok(api.analyze(partial.scenes).completeWords===false,'partial words must disable word shares');
ok(api.parse('A | Noa | hola').errors.length===1,'invalid words');
ok(api.parse('A | Noa | 10 | extra').errors.length===1,'extra column');
console.log('tests/test-pov-distribucion: OK');
