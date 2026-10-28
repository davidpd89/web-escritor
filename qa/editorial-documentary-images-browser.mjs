import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const origin=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const cases=[
  ['/autor.html','.author-portrait img'],
  ['/prensa.html','img[src*="retrato-editorial-prensa"]'],
  ['/eventos.html','img[src*="feria-libro-madrid-2026-caseta-337"]']
];
try {
  for(const [route,selector] of cases){
    const page=await browser.newPage({viewport:{width:390,height:844}});
    try {
      const response=await page.goto(origin+route,{waitUntil:'domcontentloaded'});
      assert.ok(response?.ok(),`${route}: HTTP ${response?.status()}`);
      const img=page.locator(selector);
      assert.equal(await img.count(),1,`${route}: falta imagen ${selector}`);
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(el=>el.decode());
      const state=await img.evaluate(el=>({alt:el.getAttribute('alt'),width:el.naturalWidth,height:el.naturalHeight,visible:el.getBoundingClientRect().width>0}));
      assert.ok(state.width>0&&state.height>0,`${route}: imagen ${selector} no carga`);
      assert.ok(state.visible,`${route}: imagen ${selector} sin tamaño visible`);
      assert.ok(state.alt?.trim().length>=12,`${route}: imagen documental sin alternativa descriptiva: ${state.alt}`);
    }finally{await page.close();}
  }
}finally{await browser.close();}
console.log('PASS: fotografías documentales accesibles');