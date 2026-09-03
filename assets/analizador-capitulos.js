import { csvDecimal } from '/assets/analizador-capitulos-engine.js';

const MAX_BYTES = 8 * 1024 * 1024;
const tool = document.querySelector('[data-chapter-analyzer]');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}
function fmt(n, digits=0) { return Number(n || 0).toLocaleString('es-ES',{maximumFractionDigits:digits,minimumFractionDigits:digits}); }
function parseNames(value) { return [...new Set(String(value||'').split(/[\n,;]+/).map(v=>v.trim()).filter(Boolean))].slice(0,40); }
function naturalSort(files) { return [...files].sort((a,b)=>a.name.localeCompare(b.name,'es',{numeric:true,sensitivity:'base'})); }
function stripExtension(name) { return name.replace(/\.(?:txt|md|markdown)$/i,''); }

function splitPasted(text) {
  const clean = String(text||'').replace(/\r\n?/g,'\n').trim();
  if (!clean) return [];
  const lines = clean.split('\n');
  const markers = [];
  lines.forEach((line, i) => {
    if (/^\s*(?:#{1,3}\s*)?(?:cap[ií]tulo|chapter)\s+(?:\d+|[ivxlcdm]+)\b.*$/iu.test(line)) markers.push(i);
  });
  if (markers.length < 2) return [{id:'paste-1',title:'Texto pegado',sourceName:'texto pegado',text:clean}];
  const chapters = [];
  for (let x=0; x<markers.length; x+=1) {
    const start=markers[x], end=x+1<markers.length?markers[x+1]:lines.length;
    const title=lines[start].replace(/^\s*#{1,3}\s*/,'').trim();
    chapters.push({id:`paste-${x+1}`,title,sourceName:'texto pegado',text:lines.slice(start+1,end).join('\n').trim()});
  }
  return chapters.filter(c=>c.text);
}

async function chaptersFromFiles(fileList) {
  const files = naturalSort(fileList).filter(f => /\.(txt|md|markdown)$/i.test(f.name) || /^text\//.test(f.type));
  const bytes = files.reduce((sum,f)=>sum+f.size,0);
  if (bytes > MAX_BYTES) throw new Error('El conjunto supera 8 MB. Divide el manuscrito en dos análisis para evitar problemas de memoria en móvil.');
  return Promise.all(files.map(async (file, index)=>({id:`file-${index+1}`,title:stripExtension(file.name),sourceName:file.name,text:await file.text()})));
}

function renderBars(result, root) {
  const wrap=root.querySelector('[data-chapter-chart]');
  const max=Math.max(1,...result.chapters.map(c=>c.words));
  wrap.innerHTML=result.chapters.map(c=>`<div class="chapter-bar-row"><span class="chapter-bar-label">${escapeHtml(c.title)}</span><span class="chapter-bar-track"><span class="chapter-bar-fill" style="--bar:${(c.words/max*100).toFixed(2)}%"></span></span><strong>${fmt(c.words)}</strong></div>`).join('');
}

function renderTable(result, root, names) {
  const headNames=names.map(n=>`<th scope="col">${escapeHtml(n)}</th>`).join('');
  root.querySelector('[data-chapter-table]').innerHTML=`<table><thead><tr><th scope="col">Capítulo</th><th scope="col">Palabras</th><th scope="col">Acumulado</th><th scope="col">Vs. mediana</th><th scope="col">Párrafo mediano</th><th scope="col">Diálogo aprox.</th><th scope="col">Separadores</th>${headNames}</tr></thead><tbody>${result.chapters.map(c=>`<tr><th scope="row">${escapeHtml(c.title)}</th><td>${fmt(c.words)}</td><td>${fmt(c.cumulativeWords)} · ${fmt(c.cumulativePercentage,1)} %</td><td>${c.deviationFromMedianPct>=0?'+':''}${fmt(c.deviationFromMedianPct,1)} %</td><td>${fmt(c.medianParagraphWords,1)}</td><td>${fmt(c.dialoguePercentage,1)} %</td><td>${fmt(c.explicitSceneBreaks)}</td>${names.map(n=>`<td>${fmt(c.mentions[n]||0)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function render(result, names) {
  const root=document.querySelector('[data-chapter-results]');
  root.hidden=false;
  root.querySelector('[data-chapter-summary]').innerHTML=[['Capítulos',result.chapterCount],['Palabras',fmt(result.totalWords)],['Mediana/capítulo',fmt(result.medianWords)],['Media/capítulo',fmt(result.meanWords)],['Mín.–máx.',`${fmt(result.minWords)}–${fmt(result.maxWords)}`],['Variación relativa',`${fmt(result.coefficientVariationPct,1)} %`]].map(([k,v])=>`<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
  renderBars(result,root); renderTable(result,root,names);
  root.querySelector('[data-chapter-note]').textContent='Las diferencias entre capítulos son descriptivas. Un capítulo más corto, más largo o con más diálogo no es un error por sí mismo.';
}

function csvEscape(v) { const s=String(v??''); return /[";\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s; }
function exportCsv(result,names) {
  const headers=['capitulo','palabras','acumulado','porcentaje_acumulado','desviacion_mediana_pct','parrafos','parrafo_medio','parrafo_mediano','parrafo_mas_largo','dialogo_pct','separadores_escena',...names.map(n=>`menciones_${n}`)];
  const rows=result.chapters.map(c=>[c.title,c.words,c.cumulativeWords,csvDecimal(c.cumulativePercentage),csvDecimal(c.deviationFromMedianPct),c.paragraphs,csvDecimal(c.avgParagraphWords),csvDecimal(c.medianParagraphWords),c.longestParagraphWords,csvDecimal(c.dialoguePercentage),c.explicitSceneBreaks,...names.map(n=>c.mentions[n]||0)]);
  const csv='\uFEFF'+[headers,...rows].map(r=>r.map(csvEscape).join(';')).join('\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a'); a.href=url; a.download='analisis-capitulos.csv'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),0);
}

if (tool) {
  const files=tool.querySelector('[data-chapter-files]'), paste=tool.querySelector('[data-chapter-paste]'), namesInput=tool.querySelector('[data-chapter-names]'), status=tool.querySelector('[data-chapter-status]');
  let last=null, lastNames=[];
  tool.addEventListener('submit', async e=>{
    e.preventDefault(); status.textContent='Analizando…';
    try {
      let chapters=files.files.length?await chaptersFromFiles(files.files):splitPasted(paste.value);
      if (!chapters.length) throw new Error('Añade archivos .txt/.md o pega un manuscrito.');
      lastNames=parseNames(namesInput.value);
      const worker=new Worker('/assets/analizador-capitulos.worker.js',{type:'module'});
      const result=await new Promise((resolve,reject)=>{ worker.onmessage=ev=>ev.data?.ok?resolve(ev.data.result):reject(new Error(ev.data?.error||'No se pudo analizar.')); worker.onerror=()=>reject(new Error('No se pudo iniciar el analizador.')); worker.postMessage({chapters,names:lastNames}); });
      worker.terminate(); last=result; render(result,lastNames); status.textContent=`${result.chapterCount} capítulos analizados. El texto no se ha enviado a ningún servidor.`;
      const chapterBand=result.chapterCount<=5?'1_5':result.chapterCount<=20?'6_20':'gt20';
      const wordBand=result.totalWords<20000?'lt20k':result.totalWords<80000?'20k_79k':'gte80k';
      window.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event:'chapter_analyzer_run',target:`${chapterBand}|${wordBand}`}}));
    } catch(err) { status.textContent=err.message; }
  });
  tool.querySelector('[data-chapter-clear]').addEventListener('click',()=>{files.value='';paste.value='';namesInput.value='';document.querySelector('[data-chapter-results]').hidden=true;status.textContent='';last=null;});
  document.querySelector('[data-chapter-export]').addEventListener('click',()=>{if(last) exportCsv(last,lastNames);});
}
