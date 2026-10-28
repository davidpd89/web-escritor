import assert from 'node:assert/strict';
import {chromium,firefox,webkit} from 'playwright';
import {readKeyboardFocusState} from './keyboard-focus-state.mjs';

for(const [name,engine] of Object.entries({chromium,firefox,webkit})){
  const browser=await engine.launch({headless:true});
  try{
    const page=await browser.newPage({viewport:{width:800,height:600}});
    await page.setContent('<button id="target" style="opacity:0">Invisible</button>');
    await page.focus('#target');
    const transparent=await page.evaluate(readKeyboardFocusState);
    assert.equal(transparent.ok,false,`${name}: opacity:0 produce falso positivo`);

    await page.setContent('<button id="target" style="position:absolute;left:20px;top:20px;width:150px;height:50px">Cubierto</button>');
    await page.focus('#target');
    await page.evaluate(()=>{
      const cover=document.createElement('div');
      cover.style.cssText='position:fixed;inset:0;background:white;z-index:9999;pointer-events:auto';
      document.body.append(cover);
    });
    const covered=await page.evaluate(readKeyboardFocusState);
    assert.equal(covered.ok,false,`${name}: foco completamente ocluido aceptado`);
    await page.close();
  }finally{await browser.close();}
}
console.log('PASS focus visibility adversarial');