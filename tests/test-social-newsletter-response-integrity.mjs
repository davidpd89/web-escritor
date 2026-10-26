import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync('assets/newsletter-general.js', 'utf8');
const cases = [
  ['confirmed pending', 200, {ok:true,state:'pending_confirmation'}, true],
  ['missing state', 200, {ok:true}, false],
  ['contradictory state', 200, {ok:false,state:'pending_confirmation'}, false],
  ['empty success', 200, {}, false],
  ['invalid request', 400, {ok:true,state:'pending_confirmation'}, false],
  ['rate limited', 429, {ok:true,state:'pending_confirmation'}, false],
  ['server failure', 500, {ok:true,state:'pending_confirmation'}, false]
];

for (const [label, status, body, expected] of cases) {
  test(`newsletter: ${label}`, async () => {
    const window = {location:{hostname:'davidportodiaz.com'}};
    const context = vm.createContext({
      window,
      document:{readyState:'loading',addEventListener(){}},
      navigator:{onLine:true},
      AbortController,
      setTimeout,
      clearTimeout,
      fetch:async () => ({
        ok:status >= 200 && status < 300,
        status,
        json:async () => body
      })
    });
    vm.runInContext(source, context, {filename:'assets/newsletter-general.js'});
    const result = await window.DPNewsletterGeneral.postNewsletter({
      email:'lector@example.com',source:'explore',website:''
    });
    assert.equal(result.ok, expected, `newsletter: ${label}, HTTP ${status}`);
    if (expected) assert.equal(result.state,'pending_confirmation');
  });
}