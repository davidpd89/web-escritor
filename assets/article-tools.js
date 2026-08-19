// Article Tools - minimal, non-invasive
(function(){
  'use strict';

  // Helper: safe query
  const $ = (sel, ctx=document) => ctx.querySelector(sel);
  const $$ = (sel, ctx=document) => Array.from(ctx.querySelectorAll(sel));

  // Ensure we only run once
  if (window.__articleToolsLoaded) return; window.__articleToolsLoaded = true;

  // Find main content area
  const main = document.getElementById('main-content');
  if (!main) return;

  // Do not duplicate global reading progress (script.js uses .reading-progress)
  const hasGlobalProgress = !!document.querySelector('.reading-progress');

  // Build container
  const container = document.getElementById('article-tools') || (() => {
    const el = document.createElement('div'); el.id = 'article-tools'; el.className = 'article-tools'; el.setAttribute('role','region'); el.setAttribute('aria-label','Herramientas de lectura');
    // insert before first section inside main
    const firstSection = main.querySelector('.section');
    if (firstSection && firstSection.parentNode) firstSection.parentNode.insertBefore(el, firstSection);
    else main.insertBefore(el, main.firstChild);
    return el;
  })();

  // Collect headings for TOC (h2, h3 within main)
  const headings = $$('#main-content h2, #main-content h3').filter(h => h.id || (h.textContent && h.textContent.trim().length>0));

  // Controls: TOC (only if >=2 headings), Share
  const tocWrap = document.createElement('div'); tocWrap.className = 'at-toc';
  const controls = document.createElement('div'); controls.className = 'at-controls';

  // TOC
  if (headings.length >= 2){
    const tocTitle = document.createElement('strong'); tocTitle.textContent = 'En esta página'; tocWrap.appendChild(tocTitle);
    const list = document.createElement('ol'); list.className = 'at-toc-list';
    headings.forEach(h => {
      if (!h.id){
        // create id from text
        h.id = h.textContent.trim().toLowerCase().replace(/[^a-z0-9\-]+/gi,'-').replace(/^-+|-+$/g,'');
      }
      const li = document.createElement('li');
      const a = document.createElement('a'); a.href = '#'+h.id; a.textContent = h.textContent.trim(); a.className='at-toc-link';
      a.addEventListener('click', (e)=>{ e.preventDefault(); document.getElementById(h.id).scrollIntoView({behavior:'smooth'}); history.replaceState(null,'', '#'+h.id); });
      li.appendChild(a); list.appendChild(li);
    });
    tocWrap.appendChild(list);
  }

  // Share control
  const shareWrap = document.createElement('div'); shareWrap.className = 'at-share';
  const shareBtn = document.createElement('button'); shareBtn.className='at-btn'; shareBtn.type='button'; shareBtn.textContent='Compartir';
  shareBtn.addEventListener('click', async ()=>{
    const url = (document.querySelector('link[rel="canonical"]')||{}).href || location.href;
    const title = document.title || document.querySelector('h1')?.textContent || '';
    if (navigator.share){
      try{ await navigator.share({title, text: title, url}); dispatchShareEvent('share'); return; }catch(e){ /* fallthrough to fallback */ }
    }
    // Fallback: copy link
    try{ await navigator.clipboard.writeText(url); showTempLabel(shareBtn,'Enlace copiado'); dispatchShareEvent('copy'); }
    catch(e){ prompt('Enlace para compartir (copiar):', url); dispatchShareEvent('prompt'); }
  });
  shareWrap.appendChild(shareBtn);

  // Print control
  const printWrap = document.createElement('div'); printWrap.className = 'at-print';
  const printBtn = document.createElement('button');
  printBtn.className = 'at-btn';
  printBtn.type = 'button';
  printBtn.textContent = 'Imprimir / PDF';
  printBtn.setAttribute('aria-label', 'Imprimir o guardar como PDF');
  printBtn.addEventListener('click', ()=>{
    if (!document.querySelector('link[href="/assets/article-print.css"]')){
      const l = document.createElement('link');
      l.rel = 'stylesheet';
      l.href = '/assets/article-print.css';
      l.media = 'print';
      document.head.appendChild(l);
    }
    ensurePrintSource();
    try{ window.print(); dispatchShareEvent('print'); }catch(e){}
  });

  function ensurePrintSource(){
    if (document.querySelector('.print-source')) return;
    const url = (document.querySelector('link[rel="canonical"]')||{}).href || location.href;
    const title = document.querySelector('h1')?.textContent?.trim() || document.title || '';
    const el = document.createElement('p');
    el.className = 'print-source';
    el.setAttribute('aria-hidden', 'true');
    el.textContent = title ? `${title} — ${url}` : url;
    const host = main.querySelector('[data-printable]') || main;
    host.appendChild(el);
  }
  printWrap.appendChild(printBtn);
  controls.appendChild(printWrap);

  // Optionally add progress toggle if no global progress exists
  if (!hasGlobalProgress){
    const progBtn = document.createElement('button'); progBtn.className='at-btn'; progBtn.type='button'; progBtn.textContent='Mostrar progreso';
    let progEl = null;
    progBtn.addEventListener('click', ()=>{
      if (!progEl){ progEl = document.createElement('div'); progEl.className='at-local-progress'; progEl.style.height='4px'; progEl.style.background='var(--accent)'; progEl.style.width='0%'; progEl.style.borderRadius='4px'; progEl.style.marginTop='6px'; container.appendChild(progEl);
        // attach scroll handler
        const update = ()=>{ const scrollTop=window.scrollY; const docHeight=document.documentElement.scrollHeight-window.innerHeight; progEl.style.width = docHeight>0 ? (scrollTop/docHeight*100)+'%' : '0%'; };
        window.addEventListener('scroll', throttle(update, 100), {passive:true}); update();
        progBtn.textContent='Ocultar progreso';
      } else { progEl.remove(); progEl=null; progBtn.textContent='Mostrar progreso'; }
    });
    controls.appendChild(progBtn);
  }

  controls.appendChild(shareWrap);

  // Utility: show temp label on button
  function showTempLabel(btn, text){ const orig = btn.textContent; btn.textContent = text; setTimeout(()=>btn.textContent=orig,2000); }

  // Utility: dispatch dp:analytics custom event (non-blocking)
  function dispatchShareEvent(action){ try{ const ev = new CustomEvent('dp:analytics', {detail:{category:'article-tools', action}}); window.dispatchEvent(ev);}catch(e){} }

  // Throttle
  function throttle(fn, wait){ let t=0; return function(){ const now=Date.now(); if (now-t>wait){ t=now; fn.apply(this,arguments); } }; }

  // Simple scheduleTask polyfill reference to existing page scheduler if any
  function scheduleTask(fn){ if (window.requestIdleCallback) requestIdleCallback(fn); else setTimeout(fn,150); }

  // Compose UI
  container.appendChild(tocWrap);
  container.appendChild(controls);

})();
