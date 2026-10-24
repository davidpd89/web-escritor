import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

for (const mode of ['click','space']) {
  await withPage(async ({page}) => {
    const trigger = page.locator('.microstory-actions [data-email-reveal]');
    assert.equal(await trigger.count(),1);
    assert.equal(await trigger.getAttribute('href'),'/prensa.html#contacto');
    assert.match(await trigger.getAttribute('data-email-subject'),/Al otro lado/);
    if (mode === 'click') await trigger.click({noWaitAfter:true});
    else {await trigger.focus();await page.keyboard.press('Space');}
    await page.waitForFunction(() => !!document.querySelector('.microstory-actions a[data-email-revealed=true]'));
    const state = await page.locator('.microstory-actions a[data-email-revealed=true]').evaluate(a => ({href:a.getAttribute('href'),label:a.getAttribute('aria-label'),focused:document.activeElement===a,original:a.hasAttribute('data-email-reveal')}));
    assert.ok(state.href.startsWith('mailto:'),mode);
    const url = new URL(state.href);
    assert.ok(url.pathname.includes('@'));
    assert.match(url.searchParams.get('subject') || '',/Copia de la antología.*Al otro lado/);
    assert.match(state.label,/correo|@/i);
    assert.equal(state.focused,true);
    assert.equal(state.original,false);
    assert.equal(new URL(page.url()).pathname,'/al-otro-lado/');
  });
}
console.log('PASS microstory contact journey');
