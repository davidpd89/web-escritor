import assert from 'node:assert/strict';

const CANON='https://davidportodiaz.com';
const cases=[
  ['http://davidportodiaz.com/', '/'],
  ['http://davidportodiaz.com/editoriales/', '/editoriales/'],
  ['http://davidportodiaz.com/convocatorias-escritores/', '/convocatorias-escritores/'],
  ['https://www.davidportodiaz.com/', '/'],
  ['https://www.davidportodiaz.com/editoriales/', '/editoriales/'],
  ['http://www.davidportodiaz.com/convocatorias-escritores/', '/convocatorias-escritores/'],
];

async function fetchRetry(url){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(url,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-origin-normalization-audit/1.0'},
        signal:AbortSignal.timeout(20000),
      });
      last=r;
      if(r.status!==429&&(r.status<500||r.status>599))return r;
    }catch(e){last=e}
    if(i<2)await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  if(last instanceof Response)return last;
  throw last;
}

const failures=[];
for(const [input,path] of cases){
  try{
    const r=await fetchRetry(input);
    assert.equal(r.status,200,`${input}: final HTTP ${r.status}`);
    const u=new URL(r.url);
    assert.equal(u.origin,CANON,`${input}: final origin ${u.origin}`);
    assert.equal(u.pathname,path,`${input}: final path ${u.pathname}`);
    console.log(`PASS ${input} -> ${u.href}`);
  }catch(e){
    failures.push(String(e?.message||e));
  }
}

for(const path of ['/editoriales','/convocatorias-escritores','/metodologia-editorial']){
  try{
    const r=await fetchRetry(CANON+path);
    assert.equal(r.status,200,`${path}: final HTTP ${r.status}`);
    const u=new URL(r.url);
    assert.equal(u.origin,CANON,`${path}: final origin`);
    assert.equal(u.pathname,path+'/',`${path}: missing-slash normalization`);
    console.log(`PASS ${path} -> ${u.pathname}`);
  }catch(e){failures.push(String(e?.message||e))}
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production origin/protocol/slash normalization');
