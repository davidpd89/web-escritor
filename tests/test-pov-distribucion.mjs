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

// O.2: formato V1 documentado "POV | palabras" (totales agregados, NO
// escenas) -- parser/analyze explicitos y separados, sin reinterpretar
// silenciosamente el formato de 2 columnas ya existente (escena | POV).
{
  const totalsInput = ['Ana | 3000', 'Bruno | 2000'].join('\n');
  const parsedTotals = api.parseTotals(totalsInput);
  ok(parsedTotals.errors.length === 0, 'parseTotals: sin errores para entrada válida');
  ok(parsedTotals.totals.length === 2, 'parseTotals: 2 filas');
  const t = api.analyzeTotals(parsedTotals.totals);
  ok(t.mode === 'totals', 'analyzeTotals: mode=totals');
  ok(t.totalWords === 5000, 'analyzeTotals: total palabras');
  const anaTotal = t.povs.find(p => p.pov === 'Ana');
  ok(Math.abs(anaTotal.wordShare - 0.6) < 1e-9, 'analyzeTotals: wordShare de Ana');

  // El formato "escena | POV" documentado como "Ana | Bruno" (2 columnas)
  // NO debe confundirse con "POV | palabras": la segunda columna debe ser
  // un entero, así que "Ana | Bruno" con parseTotals debe fallar con un
  // mensaje claro, no interpretarse silenciosamente como palabras=0.
  const wrongFormat = api.parseTotals('Ana | Bruno');
  ok(wrongFormat.errors.length === 1, 'parseTotals: rechaza una segunda columna no numérica');

  // POV duplicado: rechazado explícitamente (una sola línea por POV en este formato).
  const dup = api.parseTotals('Ana | 100\nAna | 200');
  ok(dup.errors.length === 1, 'parseTotals: rechaza POV duplicado');

  // El formato de escenas no se ve afectado por la existencia del nuevo formato.
  const scenesStillWork = api.parse('A | Ana | 1000\nB | Bruno | 500');
  ok(scenesStillWork.errors.length === 0, 'parse (escenas) sigue funcionando igual');
}

console.log('tests/test-pov-distribucion: OK');
