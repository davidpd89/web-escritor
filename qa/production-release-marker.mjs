import assert from 'node:assert/strict';

export async function assertProductionRelease({origin, sha, label='release', attempts=8, delayMs=1500, timeoutMs=15000}) {
  const expected=String(sha||'').trim().toLowerCase();
  if(!expected) return;
  const base=String(origin||'').replace(/\/$/,'');
  let lastError=null;
  for(let attempt=1;attempt<=attempts;attempt++){
    try{
      const url=`${base}/_release/${expected}.json?qa_release=${encodeURIComponent(label)}&attempt=${attempt}`;
      const response=await fetch(url,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-production-release-marker/1.0'},
        signal:AbortSignal.timeout(timeoutMs),
      });
      if(response.status===200){
        const body=await response.json();
        assert.deepEqual(body,{schemaVersion:1,sha:expected},'release marker mismatch');
        return;
      }
      lastError=new Error(`release marker HTTP ${response.status} (attempt ${attempt}/${attempts})`);
    }catch(error){
      lastError=error;
    }
    if(attempt<attempts) await new Promise(resolve=>setTimeout(resolve,delayMs*attempt));
  }
  throw new Error(`release marker unavailable after ${attempts} attempts: ${lastError?.message||lastError}`);
}
