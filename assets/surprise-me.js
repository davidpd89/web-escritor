(() => {
  'use strict';
  const items = Array.isArray(window.DP_SURPRISE_CONTENT) ? window.DP_SURPRISE_CONTENT : [];
  const buttons = document.querySelectorAll('[data-surprise-me]');
  if (!items.length || !buttons.length) return;

  const KEY='dp_surprise_recent_v1';
  function readRecent(){
    try { const x=JSON.parse(sessionStorage.getItem(KEY)||'[]'); return Array.isArray(x)?x.slice(0,3):[]; } catch(_) { return []; }
  }
  function writeRecent(urls){ try { sessionStorage.setItem(KEY, JSON.stringify(urls.slice(0,3))); } catch(_) {} }
  function rand(max){
    if (max<=1) return 0;
    if (window.crypto?.getRandomValues) { const a=new Uint32Array(1); window.crypto.getRandomValues(a); return a[0]%max; }
    return Math.floor(Math.random()*max);
  }
  function normalPath(path){ return String(path||'/').replace(/\/index\.html$/,'/'); }
  function pick(audience){
    const current=normalPath(location.pathname); const recent=readRecent();
    let pool=items.filter(x => x.url!==current && (x.audiences.includes(audience)||x.audiences.includes('all')) && !recent.includes(x.url));
    if (!pool.length) pool=items.filter(x => x.url!==current && (x.audiences.includes(audience)||x.audiences.includes('all')));
    if (!pool.length) pool=items.filter(x=>x.url!==current);
    return pool.length ? pool[rand(pool.length)] : null;
  }
  buttons.forEach(button => {
    button.addEventListener('click', event => {
      const audience=button.dataset.surpriseAudience||'all'; const item=pick(audience);
      if (!item) return;
      event.preventDefault();
      writeRecent([item.url,...readRecent().filter(x=>x!==item.url)]);
      document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event:'surprise_me',target:item.type}}));
      location.assign(item.url);
    });
  });
})();
