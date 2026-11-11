import assert from 'node:assert/strict';
import http from 'node:http';
process.env.EXPECTED_RELEASE_SHA='ABC123';
process.env.QA_SLOW_COOLDOWN_MS='300';
const { auditUrl, currentGapMs, fetchStats, fetchWithBackoff, isTransientStatus } = await import('../qa/production-fetch.mjs');

// Clave anti-caché común por release: conserva la query y usa el SHA auditado.
assert.equal(auditUrl('/assets/a.js?v=4','https://example.test').href,'https://example.test/assets/a.js?v=4&__qa_release=abc123');
assert.equal(auditUrl('https://example.test/x/').href,'https://example.test/x/?__qa_release=abc123');

// Servidor local: /rate da 429 con Retry-After: 1 la primera vez; /other anota cuándo llega cada petición.
const hits={};
let rateLimitedAt=0, otherAt=0, signalRateLimited, laneInFlight=0, laneMax=0;
const rateLimited=new Promise(r=>{signalRateLimited=r});
const srv=http.createServer((q,s)=>{
  const p=q.url.split('?')[0];
  hits[p]=(hits[p]||0)+1;
  if(p==='/rate'&&hits[p]===1){
    rateLimitedAt=Date.now();
    s.statusCode=429;s.setHeader('retry-after','1');s.end('slow down');
    return signalRateLimited();
  }
  if(p==='/other') otherAt=Date.now();
  // Cuota de GitHub Pages: 429 más veces que los intentos normales y luego 200.
  if(p==='/stubborn'&&hits[p]<=2){s.statusCode=429;s.setHeader('retry-after','1');return s.end('slow down')}
  if(p==='/always429'){s.statusCode=429;s.setHeader('retry-after','1');return s.end('slow down')}
  if(p.startsWith('/lane')){
    if(hits[p]===1){s.statusCode=429;s.setHeader('retry-after','1');return s.end('slow down')}
    laneInFlight++;laneMax=Math.max(laneMax,laneInFlight);
    return setTimeout(()=>{laneInFlight--;s.end(`ok ${p}`)},200);
  }
  if(p==='/missing'){s.statusCode=404;return s.end('no')}
  if(p==='/down'){s.statusCode=503;return s.end('down')}
  s.end(`ok ${p}`);
});
await new Promise(r=>srv.listen(0,'127.0.0.1',r));
const o=`http://127.0.0.1:${srv.address().port}`;

assert.equal(isTransientStatus(429),true);
assert.equal(isTransientStatus(503),true);
assert.equal(isTransientStatus(404),false);

// Un 404 vuelve al primer intento, sin reintentos.
const missing=await fetchWithBackoff(`${o}/missing`);
assert.equal(missing.status,404);
assert.equal(hits['/missing'],1);

// Un 5xx persistente devuelve el último estado tras agotar los intentos (no lanza).
const down=await fetchWithBackoff(`${o}/down`,{},{attempts:2});
assert.equal(down.status,503);
assert.equal(hits['/down'],2);

// Un 429 pausa también a los demás hilos hasta que pasa el Retry-After.
const first=fetchWithBackoff(`${o}/rate`);
await rateLimited;
await new Promise(r=>setTimeout(r,100)); // a que el cliente lea el 429 y anote la pausa
const other=await fetchWithBackoff(`${o}/other`,{},{read:'buffer'});
assert.equal(other.status,200);
assert.ok(Buffer.isBuffer(other.body));
assert.ok(otherAt-rateLimitedAt>=900,`/other llegó ${otherAt-rateLimitedAt} ms después del 429; debía esperar al Retry-After`);
const rate=await first;
assert.equal(rate.status,200);
assert.equal(rate.body,'ok /rate');
assert.equal(hits['/rate'],2);
// Ritmo adaptativo: el 429 abrió una separación mínima entre peticiones.
assert.equal(fetchStats.rateLimited,1);
assert.equal(fetchStats.maxGapMs,50);

// Carril lento: un 429 que dura más que los intentos normales no se da por fallo de la web.
const stubborn=await fetchWithBackoff(`${o}/stubborn`,{},{attempts:2});
assert.equal(stubborn.status,200,'el 429 persistente debe recuperarse en el carril lento');
assert.equal(hits['/stubborn'],3);
assert.equal(fetchStats.slowRecovered,1);

// Si la cuota no cede, devuelve el 429 tras los intentos del carril lento (no lanza ni se queda colgado).
const always=await fetchWithBackoff(`${o}/always429`,{},{attempts:1,slowAttempts:2});
assert.equal(always.status,429);
assert.equal(hits['/always429'],3);

// En el carril lento las URL van de una en una.
const lanes=await Promise.all(['/lane-a','/lane-b','/lane-c'].map(p=>fetchWithBackoff(`${o}${p}`,{},{attempts:1})));
assert.deepEqual(lanes.map(x=>x.status),[200,200,200]);
assert.equal(laneMax,1,`el carril lento solapó ${laneMax} peticiones`);

// Tras la tormenta (el carril lento dejó la separación en 1 s) el ritmo vuelve a ser libre en pocas respuestas.
assert.equal(currentGapMs(),1000);
for(let i=0;i<50;i++) await fetchWithBackoff(`${o}/x`,{},{read:'none'});
assert.equal(currentGapMs(),0,`tras 50 respuestas buenas la separación sigue en ${currentGapMs()} ms`);

// read:'none' descarta el cuerpo.
assert.equal((await fetchWithBackoff(`${o}/x`,{},{read:'none'})).body,null);

// Sin respuesta (puerto cerrado) lanza el último error.
srv.close();
await assert.rejects(fetchWithBackoff(`${o}/gone`,{},{attempts:1,timeoutMs:2000}));
console.log('PASS production fetch backoff selftest');
