import assert from 'node:assert/strict';

// If the exact marker never appears, the release may simply have been superseded
// (deploy-pages uses cancel-in-progress, so a newer push replaces/cancels it).
// In that case the newer main tip's marker is live and auditing the stale SHA is
// a false positive. If the tip is the expected SHA, or the tip marker is not live
// either, the original failure is kept.
async function tipSuperseded({base, expected, tipUrl, timeoutMs}) {
  try {
    const headers={'user-agent':'david-porto-production-release-marker/1.0',accept:'application/vnd.github+json'};
    if(process.env.GITHUB_TOKEN) headers.authorization=`Bearer ${process.env.GITHUB_TOKEN}`;
    const r=await fetch(tipUrl,{headers,signal:AbortSignal.timeout(timeoutMs)});
    if(r.status!==200) return null;
    const tip=String((await r.json()).sha||'').trim().toLowerCase();
    if(!/^[0-9a-f]{40}$/.test(tip)||tip===expected) return null;
    const m=await fetch(`${base}/_release/${tip}.json?qa_release=tip`,{headers:{'cache-control':'no-cache'},signal:AbortSignal.timeout(timeoutMs)});
    if(m.status!==200) return null;
    assert.deepEqual(await m.json(),{schemaVersion:1,sha:tip});
    return tip;
  }catch{return null}
}

export async function assertProductionRelease({origin, sha, label='release', attempts=8, delayMs=1500, timeoutMs=15000, tipUrl}) {
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
        return {superseded:false};
      }
      lastError=new Error(`release marker HTTP ${response.status} (attempt ${attempt}/${attempts})`);
    }catch(error){
      lastError=error;
    }
    if(attempt<attempts) await new Promise(resolve=>setTimeout(resolve,delayMs*attempt));
  }
  const repo=process.env.GITHUB_REPOSITORY;
  const url=tipUrl||(repo?`https://api.github.com/repos/${repo}/commits/main`:'');
  if(url){
    const tip=await tipSuperseded({base,expected,tipUrl:url,timeoutMs});
    if(tip){
      console.warn(`WARN [${label}] release ${expected} superseded by live main ${tip}; marker audit skipped`);
      return {superseded:true,tip};
    }
  }
  throw new Error(`release marker unavailable after ${attempts} attempts: ${lastError?.message||lastError}`);
}
