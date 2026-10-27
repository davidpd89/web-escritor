import assert from 'node:assert/strict';
import http from 'node:http';
import { assertProductionRelease } from '../qa/production-release-marker.mjs';

const OLD='a'.repeat(40), TIP='b'.repeat(40);
let tipSha=TIP;
const srv=http.createServer((q,s)=>{
  const p=q.url.split('?')[0];
  if(p==='/tip'){s.setHeader('content-type','application/json');return s.end(JSON.stringify({sha:tipSha}))}
  if(p===`/_release/${TIP}.json`){s.setHeader('content-type','application/json');return s.end(JSON.stringify({schemaVersion:1,sha:TIP}))}
  s.statusCode=404;s.end('no');
});
await new Promise(r=>srv.listen(0,'127.0.0.1',r));
const o=`http://127.0.0.1:${srv.address().port}`;
const opt={attempts:2,delayMs:1,timeoutMs:2000};
assert.equal((await assertProductionRelease({origin:o,sha:TIP,...opt})).superseded,false);
// stale sha, newer tip live -> superseded, not a failure
assert.equal((await assertProductionRelease({origin:o,sha:OLD,tipUrl:`${o}/tip`,...opt})).superseded,true);
// stale sha without tip info -> still fails
await assert.rejects(assertProductionRelease({origin:o,sha:OLD,tipUrl:`${o}/none`,...opt}),/unavailable/);
// expected is the tip but its marker is missing -> still fails
tipSha=OLD;
await assert.rejects(assertProductionRelease({origin:o,sha:OLD,tipUrl:`${o}/tip`,...opt}),/unavailable/);
// tip marker not live -> still fails
tipSha='c'.repeat(40);
await assert.rejects(assertProductionRelease({origin:o,sha:OLD,tipUrl:`${o}/tip`,...opt}),/unavailable/);
srv.close();
console.log('PASS production release marker selftest');
