import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const browser=await chromium.launch({headless:true});
const cases=[
  ['#genero=no-existe&estado=no-existe&pais=no-existe&orden=no-existe',{genre:'',status:'',country:'',sort:'availability'}],
  ['#estado=open&directo=1',{status:'open',direct:true}],
  ['#estado=closed&orden=name',{status:'closed',sort:'name'}],
  ['#q=Minotauro',{search:'Minotauro'}],
  ['#q=%C3%91&genero=fantas%C3%ADa',{search:'Ñ',genre:'fantasía'}]
];
try {
  for(const [hash,expected] of cases) {
    const page=await browser.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto((process.env.QA_ORIGIN||'http://127.0.0.1:4173')+'/editoriales/'+hash);
    const state=await page.evaluate(()=>({genre:document.querySelector('[data-editoriales-genre]').value,status:document.querySelector('[data-editoriales-status]').value,country:document.querySelector('[data-editoriales-country]').value,sort:document.querySelector('[data-editoriales-sort]').value,direct:document.querySelector('[data-editoriales-direct]').checked,search:document.querySelector('[data-editoriales-search]').value}));
    for(const [key,value] of Object.entries(expected)) assert.equal(state[key],value,hash+' '+key);
    assert.deepEqual(errors,[],hash);
    assert.ok(await page.locator('[data-editorial-card]').count()>0);
    await page.close();
  }
  console.log('PASS fragment recovery matrix');
} finally {await browser.close();}
