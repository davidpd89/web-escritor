import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8765').replace(/\/$/,'');
const queries=['Las manecillas del recuerdo','Samuel entre mundos','editoriales','David Porto'];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  await Promise.all(Array.from({length:8},async(_,i)=>{
    const context=await browser.newContext();
    try{
      const page=await context.newPage();
      const response=await page.goto(`${BASE}/`,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`home visita ${i}: HTTP ${response?.status()}`);
      const query=queries[i%queries.length];
      const results=await page.evaluate(async q=>{
        const pf=await import('/pagefind/pagefind.js');
        const result=await pf.search(q);
        return Promise.all((result.results||[]).slice(0,5).map(async r=>{const d=await r.data();return {url:d.url,title:d.meta?.title||''};}));
      },query);
      assert(results.length>0,`Pagefind visita ${i}, consulta ${query}: sin resultados`);
      for(const r of results){
        assert(r.title.trim(),`Pagefind ${query}: título vacío para ${r.url}`);
        assert(!/\uFFFD|&(?:amp|quot|lt|gt|#\d+);/.test(r.title),`Pagefind ${query}: título mal decodificado ${r.url}: ${r.title}`);
        assert(r.url.startsWith('/')&&!r.url.startsWith('//'),`Pagefind ${query}: URL no local ${r.url}`);
        const target=await page.request.get(new URL(r.url,BASE).href);
        assert.equal(target.status(),200,`Pagefind ${query}: destino ${r.url} HTTP ${target.status()}`);
        const html=await target.text();
        assert(html.trim().length>100,`Pagefind ${query}: destino ${r.url} vacío`);
        const title=(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)||[])[1]||'';
        assert(title.trim(),`Pagefind ${query}: ${r.url} sin título HTML`);
        const normalize=s=>s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#(?:39|x27);/gi,"'").replace(/\s*\|\s*David Porto Díaz\s*$/i,'').trim().normalize('NFC');
        assert.equal(normalize(r.title),normalize(title),`Pagefind ${query}: título diferente en ${r.url}: índice=${r.title}, HTML=${title}`);
      }
    }finally{await context.close();}
  }));
  console.log('PASS concurrent Pagefind title integrity');
}finally{await browser.close();}