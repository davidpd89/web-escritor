import test from 'node:test';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.BASE_URL||process.env.SITE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');

function appearance(page,selector){
  return page.locator(selector).evaluate(el=>{
    const s=getComputedStyle(el);
    const r=el.getBoundingClientRect();
    return {outline:s.outlineStyle+' '+s.outlineWidth+' '+s.outlineColor,shadow:s.boxShadow,border:s.borderColor,background:s.backgroundColor,color:s.color,rect:{x:r.x,y:r.y,w:r.width,h:r.height},visibility:s.visibility};
  });
}

test('redes-sociales: salto y foco visible con ocho sesiones simultáneas',async()=>{
  const browser=await chromium.launch();
  try{
    await Promise.all(Array.from({length:8},async(_,i)=>{
      const context=await browser.newContext({viewport:{width:1280,height:800}});
      try{
        const page=await context.newPage();
        const response=await page.goto(BASE+'/redes-sociales/',{waitUntil:'domcontentloaded'});
        assert.equal(response.status(),200,`/redes-sociales/: sesión ${i}`);
        await page.keyboard.press('Tab');
        const skip=page.locator('a.skip-link[href="#contenido"]');
        assert.equal(await skip.evaluate(el=>el===document.activeElement),true,`/redes-sociales/: sesión ${i} salto no recibe primer foco`);
        const rect=await skip.boundingBox();
        assert.ok(rect&&rect.width>0&&rect.height>0&&rect.x+rect.width>0&&rect.y+rect.height>0,`/redes-sociales/: sesión ${i} salto no visible`);
        await page.keyboard.press('Enter');
        assert.equal(new URL(page.url()).hash,'#contenido',`/redes-sociales/: sesión ${i} salto incorrecto`);
        assert.equal(await page.locator('main#contenido').count(),1,`/redes-sociales/: sesión ${i} destino inexistente`);
        const selector='[data-network="bluesky"] h3 a';
        const before=await appearance(page,selector);
        await page.locator(selector).focus();
        const after=await appearance(page,selector);
        assert.ok(after.rect.w>0&&after.rect.h>0,`/redes-sociales/: sesión ${i} enlace sin geometría`);
        assert.ok(before.outline!==after.outline||before.shadow!==after.shadow||before.border!==after.border||before.background!==after.background||before.color!==after.color,`/redes-sociales/: sesión ${i} foco sin cambio visual`);
      }finally{await context.close();}
    }));
  }finally{await browser.close();}
});