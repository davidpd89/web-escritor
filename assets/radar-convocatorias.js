(() => {
  const items=[...document.querySelectorAll('[data-radar-item]')];
  if(!items.length)return;
  const q=document.querySelector('[data-radar-search]');
  const type=document.querySelector('[data-radar-type]');
  const genre=document.querySelector('[data-radar-genre]');
  const soon=document.querySelector('[data-radar-soon]');
  const count=document.querySelector('[data-radar-count]');
  const clear=document.querySelector('[data-radar-clear]');

  const emit=(event,detail={})=>document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event,...detail}}));
  document.addEventListener('click',(ev)=>{
    const source=ev.target.closest?.('[data-radar-source]');
    if(source)emit('radar_source_click',{opportunity_type:source.dataset.radarSourceType||'unknown'});
    if(ev.target.closest?.('[data-radar-calendar]'))emit('radar_calendar_click');
  });
  const norm=(v)=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const apply=()=>{
    const query=norm(q?.value), t=norm(type?.value), g=norm(genre?.value); let visible=0;
    items.forEach(el=>{
      const hay=norm(el.textContent), et=norm(el.dataset.type), eg=norm(el.dataset.genres);
      const ok=(!query||hay.includes(query))&&(!t||et===t)&&(!g||eg.split('|').includes(g))&&(!soon?.checked||el.querySelector('.radar-badge')?.textContent.includes('Cierra pronto'));
      el.hidden=!ok; if(ok)visible++;
    });
    if(count)count.textContent=`${visible} ${visible===1?'convocatoria':'convocatorias'} visibles`;
  };
  [q,type,genre,soon].forEach(el=>el?.addEventListener(el===q?'input':'change',apply));
  clear?.addEventListener('click',()=>{if(q)q.value='';if(type)type.value='';if(genre)genre.value='';if(soon)soon.checked=false;apply();q?.focus();});
  apply();
})();
