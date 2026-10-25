import test from 'node:test';
import assert from 'node:assert/strict';
import {planShadow} from '../scripts/qa-gate-shadow.mjs';

const paths = a => a.map(path => ({status:'M',path}));
test('documentation is minimal',()=> assert.equal(planShadow(paths(['README.md','docs/notes.md'])).mode,'minimal'));
test('own gate is minimal',()=> assert.equal(planShadow(paths(['scripts/qa-gate-shadow.mjs'])).mode,'minimal'));
test('HTML only proposes targeted including home sentinel',()=>{
  const x=planShadow(paths(['libros/index.html','privacidad.html']));
  assert.equal(x.mode,'targeted'); assert.deepEqual(x.routes,['/','/libros/','/privacidad.html']);
});
test('global CSS cannot skip comprehensive suite',()=>assert.equal(planShadow(paths(['assets/styles.css'])).mode,'full'));
test('build script cannot skip comprehensive suite',()=>assert.equal(planShadow(paths(['scripts/build-site.py'])).mode,'full'));
test('data and JSON cannot skip comprehensive suite',()=>assert.equal(planShadow(paths(['data/catalog.json'])).mode,'full'));
test('HTML plus unknown file goes full',()=>assert.equal(planShadow(paths(['libros/index.html','assets/reading.js'])).mode,'full'));
test('deletions force full',()=>assert.equal(planShadow([{status:'D',path:'libros/index.html'}]).mode,'full'));
test('renames force full',()=>assert.equal(planShadow([{status:'R',path:'a.html'}]).mode,'full'));
test('empty diff goes full',()=>assert.equal(planShadow([]).mode,'full'));
test('too many pages go full',()=>assert.equal(planShadow(paths(Array.from({length:41},(_,i)=>'dir/'+i+'.html'))).mode,'full'));
test('unknown workflow goes full',()=>assert.equal(planShadow(paths(['.github/workflows/sitewide-reflow-qa.yml'])).mode,'full'));
test('missing or malformed status goes full',()=>assert.equal(planShadow([{status:'?',path:'x.html'}]).mode,'full'));
