import { MODES, buildJsonLd, validateInput, scriptTag } from './jsonld-escritores-core.js';

const form=document.querySelector('#jsonld-form');
const modeEl=document.querySelector('#jsonld-mode');
const fields=document.querySelector('#jsonld-fields');
const output=document.querySelector('#jsonld-output');
const report=document.querySelector('#jsonld-report');
const status=document.querySelector('#jsonld-status');
const copyBtn=document.querySelector('#jsonld-copy');
const downloadBtn=document.querySelector('#jsonld-download');
const resetBtn=document.querySelector('#jsonld-reset');
const processor=document.querySelector('[data-publishing-processor]');

const bookFormats=[
  ['', 'No indicar'],
  ['https://schema.org/Paperback','Tapa blanda'],
  ['https://schema.org/Hardcover','Tapa dura'],
  ['https://schema.org/EBook','Ebook'],
  ['https://schema.org/AudiobookFormat','Audiolibro'],
  ['https://schema.org/Pamphlet','Folleto'],
];
const attendanceModes=[
  ['', 'No indicar'],
  ['https://schema.org/OfflineEventAttendanceMode','Presencial'],
  ['https://schema.org/OnlineEventAttendanceMode','Online'],
  ['https://schema.org/MixedEventAttendanceMode','Mixto'],
];

const configs={
  profile:[['name','Nombre del autor','text',true],['url','URL canónica del perfil','url',true],['pageName','Título de la página','text'],['description','Descripción visible','textarea'],['image','URL de imagen','url'],['sameAs','Perfiles oficiales sameAs (uno por línea)','textarea']],
  book:[['name','Título del libro','text',true],['url','URL canónica del libro','url',true],['description','Sinopsis/descripción visible','textarea'],['image','URL de portada','url'],['isbn','ISBN','text'],['pages','Número de páginas','number'],['datePublished','Fecha de publicación','date'],['bookFormat','Formato','select',false,bookFormats],['language','Idioma (BCP 47)','text'],['genre','Género','text'],['authorName','Autor','text',true],['authorUrl','URL del autor','url'],['publisher','Editorial','text']],
  article:[['headline','Titular','text',true],['url','URL canónica','url',true],['description','Descripción visible','textarea'],['image','URL de imagen','url'],['datePublished','Fecha de publicación','date',true],['dateModified','Fecha de modificación real','date'],['language','Idioma (BCP 47)','text'],['authorName','Autor','text',true],['authorUrl','URL del autor','url']],
  event:[['name','Nombre del evento','text',true],['url','URL canónica','url',true],['description','Descripción visible','textarea'],['image','URL de imagen','url'],['startDate','Inicio','datetime-local',true],['endDate','Fin','datetime-local'],['attendanceMode','Modalidad','select',false,attendanceModes],['locationName','Lugar','text'],['address','Dirección','text'],['city','Ciudad','text'],['country','País (código)','text'],['organizerName','Organizador','text'],['organizerUrl','URL del organizador','url']]
};

function esc(s){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function renderFields(){
  fields.innerHTML=configs[modeEl.value].map(([name,label,type,required,options])=>{
    const id=`f-${name}`;
    if(type==='textarea') return `<div class="tool-field"><label class="tool-field-label" for="${id}">${esc(label)}${required?' *':''}</label><textarea class="tool-textarea tool-textarea--small" id="${id}" name="${name}" ${required?'required':''}></textarea></div>`;
    if(type==='select') return `<div class="tool-field"><label class="tool-field-label" for="${id}">${esc(label)}${required?' *':''}</label><select class="tool-select" id="${id}" name="${name}" ${required?'required':''}>${options.map(([value,text])=>`<option value="${esc(value)}">${esc(text)}</option>`).join('')}</select></div>`;
    return `<div class="tool-field"><label class="tool-field-label" for="${id}">${esc(label)}${required?' *':''}</label><input class="tool-input" id="${id}" name="${name}" type="${type}" ${required?'required':''}></div>`;
  }).join('');
  update();
}
function data(){return Object.fromEntries(new FormData(form).entries());}
function update(){
  const d=data();
  const check=validateInput(modeEl.value,d);
  let json={};
  try{json=buildJsonLd(modeEl.value,d);}catch{}
  output.textContent=scriptTag(json);
  report.innerHTML=`<p><strong>${check.valid?'Sin errores básicos':'Revisa los errores'}</strong> · ${esc(MODES[modeEl.value].schema)}${MODES[modeEl.value].googleFeature?` · función Google documentada: ${esc(MODES[modeEl.value].googleFeature)}`:' · sin rich result dedicado documentado por Google'}</p><ul>`+
    [...check.errors.map(x=>`<li class="is-error">${esc(x)}</li>`),...check.warnings.map(x=>`<li class="is-warning">${esc(x)}</li>`),...check.info.map(x=>`<li>${esc(x)}</li>`)].join('')+
    '</ul>';
  copyBtn.disabled=!check.valid;
  downloadBtn.disabled=!check.valid;
}
form.addEventListener('input',update);
form.addEventListener('submit',e=>e.preventDefault());
modeEl.addEventListener('change',renderFields);

copyBtn.addEventListener('click',async()=>{
  try {
    await navigator.clipboard.writeText(output.textContent);
    status.textContent='JSON-LD copiado.';
    document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event:'jsonld_tool_copy',target:modeEl.value}}));
  } catch {
    status.textContent='No se pudo copiar automáticamente. Selecciona el código manualmente.';
  }
});
downloadBtn.addEventListener('click',()=>{
  const blob=new Blob([output.textContent],{type:'text/plain'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=`jsonld-${modeEl.value}.txt`;
  a.click();
  setTimeout(()=>URL.revokeObjectURL(url),0);
  status.textContent='Archivo preparado.';
});
resetBtn.addEventListener('click',()=>{
  form.reset();
  modeEl.value='profile';
  renderFields();
  status.textContent='Formulario vaciado.';
});

renderFields();
if (processor) {
  processor.inert=false;
  processor.removeAttribute('inert');
  processor.removeAttribute('aria-disabled');
}
