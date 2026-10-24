import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

for (const width of [320,375,390,540,680,704,1280]) {
  await withPage(async ({page}) => {
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow<=1,`${width}: document overflow ${overflow}px`);
    for (const pan of await page.locator('.microstory-shot__pan').all()) {
      const state = await pan.evaluate(e => ({client:e.clientWidth,scroll:e.scrollWidth,overflow:getComputedStyle(e).overflowX,tab:e.tabIndex}));
      assert.equal(state.tab,0);
      if (width<704) {
        assert.ok(state.scroll>state.client+20,`${width}: missing image overflow`);
        assert.match(state.overflow,/auto|scroll/);
        await pan.focus();
        await page.keyboard.press('ArrowRight');
        await page.waitForFunction(el => el.scrollLeft>0,await pan.elementHandle());
      } else {
        assert.ok(state.scroll<=state.client+2,`${width}: unexpected image overflow`);
      }
    }
  },width);
}
console.log('PASS microstory responsive image navigation');
