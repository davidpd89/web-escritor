import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

function luminance(rgb) {
  const values = rgb.match(/[\d.]+/g).slice(0,3).map(Number).map(v => {
    v /= 255;
    return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
  });
  return values[0]*.2126 + values[1]*.7152 + values[2]*.0722;
}
function contrast(a,b) {
  const x=luminance(a),y=luminance(b);
  return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
try {
  for(const width of [320,390,768,1440]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    try {
      const response=await page.goto(`${ORIGIN}/eventos.html`,{waitUntil:'load'});
      assert.ok(response?.ok(),`/eventos.html ${width}px: HTTP incorrecto`);
      await page.evaluate(()=>document.fonts?.ready);
      const empty=page.locator('#proximos .event-empty');
      assert.equal(await empty.count(),1,`/eventos.html ${width}px: falta el estado vacío real`);
      const result=await empty.evaluate(el=>{
        const title=el.querySelector('.event-empty__title');
        const box=el.getBoundingClientRect();
        const titleBox=title.getBoundingClientRect();
        const style=getComputedStyle(title);
        return {box:{left:box.left,right:box.right,width:box.width},title:{left:titleBox.left,right:titleBox.right,width:titleBox.width},color:style.color,fontSize:parseFloat(style.fontSize),background:getComputedStyle(el).backgroundColor,visible:style.visibility!=='hidden'&&style.display!=='none',text:title.textContent.trim()};
      });
      assert.ok(result.visible,`/eventos.html ${width}px: título oculto`);
      assert.ok(result.text.length>10,`/eventos.html ${width}px: mensaje vacío incompleto`);
      assert.ok(result.box.left>=-1&&result.box.right<=width+1,`/eventos.html ${width}px: caja fuera del viewport ${JSON.stringify(result.box)}`);
      assert.ok(result.title.left>=result.box.left-1&&result.title.right<=result.box.right+1,`/eventos.html ${width}px: título desborda ${JSON.stringify(result.title)}`);
      assert.ok(result.fontSize>=20,`/eventos.html ${width}px: título demasiado pequeño ${result.fontSize}px`);
      const ratio=contrast(result.color,'rgb(241, 249, 255)');
      assert.ok(ratio>=4.5,`/eventos.html ${width}px: contraste ${ratio.toFixed(2)}:1`);
    } finally {await context.close();}
  }
} finally {await browser.close();}
console.log('Agenda vacía: legibilidad visual OK');