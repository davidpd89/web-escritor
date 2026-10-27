import assert from 'node:assert/strict';
import { runMobileAudit } from './al-otro-lado-mobile-helper.mjs';

await runMobileAudit(async (page,width,origin) => {
  const targets=[
    'main a[href="#texto"]',
    'main a[href="#evidencia"]',
    'main .microstory-actions a[href="/prensa.html#contacto"]',
    'main .microstory-sources a'
  ];
  for (const selector of targets) {
    const links=page.locator(selector);
    const count=await links.count();
    assert(count>0,`/al-otro-lado/ ${width}px: no hay controles para ${selector}`);
    for (let i=0;i<count;i++) {
      const link=links.nth(i);
      await link.scrollIntoViewIfNeeded();
      assert(await link.isVisible(),`/al-otro-lado/ ${width}px: enlace ${selector}[${i}] invisible`);
      const data=await link.evaluate(el => {
        const r=el.getBoundingClientRect();
        const x=Math.max(r.left,0)+Math.min(r.right,innerWidth)/2-Math.max(r.left,0)/2;
        const y=(Math.max(0,r.top)+Math.min(innerHeight,r.bottom))/2;
        const hit=document.elementFromPoint(x,y);
        return {rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height},x,y,hit:!!hit && (hit===el || el.contains(hit))};
      });
      assert(data.rect.width>0 && data.rect.height>0,`/al-otro-lado/ ${width}px: enlace ${selector}[${i}] sin superficie`);
      assert(data.rect.right>0 && data.rect.left<width,`/al-otro-lado/ ${width}px: enlace ${selector}[${i}] fuera de pantalla ${JSON.stringify(data.rect)}`);
      assert(data.hit,`/al-otro-lado/ ${width}px: enlace ${selector}[${i}] tapado en (${data.x},${data.y})`);
    }
  }
  await page.locator('main a[href="#texto"]').click();
  assert.equal(new URL(page.url()).hash,'#texto',`/al-otro-lado/ ${width}px: no se llega al texto`);
  await page.locator('main a[href="#evidencia"]').click();
  assert.equal(new URL(page.url()).hash,'#evidencia',`/al-otro-lado/ ${width}px: no se llega a la evidencia`);
  const request=page.locator('main .microstory-actions a[href="/prensa.html#contacto"]');
  await request.click();
  const destination=new URL(page.url());
  assert.equal(destination.origin,origin,`/al-otro-lado/ ${width}px: solicitud sale del sitio`);
  assert.equal(destination.pathname,'/prensa.html',`/al-otro-lado/ ${width}px: solicitud no llega a prensa`);
  assert.equal(destination.hash,'#contacto',`/al-otro-lado/ ${width}px: solicitud no identifica el contacto`);
});
console.log('al-otro-lado-mobile-touch-journeys: OK');
