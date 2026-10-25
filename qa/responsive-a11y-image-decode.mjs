import assert from 'node:assert/strict';
import {withSite} from './responsive-a11y-local-fixture.mjs';

const routes=['/','/libros/','/recomendaciones/','/autor.html'];
await withSite(async({visit})=>{
  let examined=0;
  for(const route of routes){
    const page=await visit(route);
    const images=page.locator('img[src^="/assets/"]:visible');
    const count=Math.min(await images.count(),8);
    for(let i=0;i<count;i++){
      const img=images.nth(i);
      await img.scrollIntoViewIfNeeded({timeout:3000});
      const result=await img.evaluate(async el=>{
        try{await el.decode()}catch(e){return {error:String(e),src:el.currentSrc}}
        return {naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,width:Number(el.getAttribute('width')),height:Number(el.getAttribute('height')),src:el.currentSrc};
      });
      examined++;
      assert.ok(!result.error&&result.naturalWidth>0&&result.naturalHeight>0,`${route}: cannot decode ${JSON.stringify(result)}`);
      if(result.width>0&&result.height>0){
        const expected=result.naturalWidth/result.naturalHeight;
        const declared=result.width/result.height;
        assert.ok(Math.abs(expected-declared)/expected<0.03,`${route}: wrong intrinsic ratio ${JSON.stringify(result)}`);
      }
    }
  }
  assert.ok(examined>=4,`Insufficient images decoded: ${examined}`);
});
