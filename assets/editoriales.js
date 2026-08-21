(() => {
  'use strict';
  const root=document.querySelector('[data-editoriales-directory]'); if(!root)return;
  const search=root.querySelector('[data-editoriales-search]'),genre=root.querySelector('[data-editoriales-genre]'),status=root.querySelector('[data-editoriales-status]'),direct=root.querySelector('[data-editoriales-direct]'),reset=root.querySelector('[data-editoriales-reset]'),count=root.querySelector('[data-editoriales-count]'),empty=root.querySelector('[data-editoriales-empty]'),cards=[...root.querySelectorAll('[data-editorial-card]')];
  const normalize=(value='')=>String(value).toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
  const valid=(select,value)=>select&&value&&[...select.options].some(o=>o.value===value)?value:'';
  const readHash=()=>{const p=new URLSearchParams(location.hash.replace(/^#/,''));if(search)search.value=p.get('q')||'';if(genre)genre.value=valid(genre,p.get('genero')||'');if(status)status.value=valid(status,p.get('estado')||'');if(direct)direct.checked=p.get('directo')==='1';};
  const nextUrl=()=>{const p=new URLSearchParams();if(search?.value.trim())p.set('q',search.value.trim());if(genre?.value)p.set('genero',genre.value);if(status?.value)p.set('estado',status.value);if(direct?.checked)p.set('directo','1');const h=p.toString();return `${location.pathname}${location.search}${h?`#${h}`:''}`;};
  const apply=({historyMode='replace'}={})=>{const q=normalize(search?.value),g=normalize(genre?.value),s=status?.value||'',d=Boolean(direct?.checked);let visible=0;cards.forEach(card=>{const hay=normalize(`${card.dataset.name||''} ${card.dataset.group||''} ${card.dataset.genres||''} ${card.textContent||''}`),genres=normalize(card.dataset.genres||'').split('|');const ok=(!q||hay.includes(q))&&(!g||genres.includes(g))&&(!s||card.dataset.status===s)&&(!d||card.dataset.direct==='true');card.hidden=!ok;if(ok)visible++;});if(count)count.textContent=`${visible} ${visible===1?'editorial':'editoriales'}`;if(empty)empty.hidden=visible!==0;if(historyMode)history[historyMode==='push'?'pushState':'replaceState'](null,'',nextUrl());};
  search?.addEventListener('input',()=>apply({historyMode:'replace'}));[genre,status,direct].filter(Boolean).forEach(c=>c.addEventListener('change',()=>apply({historyMode:'push'})));
  reset?.addEventListener('click',()=>{if(search)search.value='';if(genre)genre.value='';if(status)status.value='';if(direct)direct.checked=false;apply({historyMode:'push'});search?.focus();});
  let lastRestoredUrl=location.href;const restore=()=>{if(location.href===lastRestoredUrl)return;lastRestoredUrl=location.href;readHash();apply({historyMode:null});};window.addEventListener('hashchange',restore);window.addEventListener('popstate',restore);
  readHash();apply({historyMode:null});
})();
