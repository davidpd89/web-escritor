import { validateEventModel, buildEventOutputs } from './evento-escritor-core.js';

const root=document.querySelector('[data-event-builder]');
if(root) init(root);

function init(root){
  const form=root.querySelector('form');
  const allDay=form.elements.allDay;
  const timed=root.querySelector('[data-timed-fields]');
  const dated=root.querySelector('[data-date-fields]');
  const status=root.querySelector('[data-event-status]');
  const results=root.querySelector('[data-event-results]');
  const htmlOut=root.querySelector('[data-event-html]');
  const jsonOut=root.querySelector('[data-event-jsonld]');
  const download=root.querySelector('[data-event-ics]');
  let current=null;

  allDay.addEventListener('change',()=>toggleMode());
  toggleMode();

  form.addEventListener('submit',(e)=>{
    e.preventDefault();
    const model=modelFromForm(form);
    const errors=validateEventModel(model);
    if(errors.length){ setStatus(errors.join(' '),true); results.hidden=true; return; }
    try{
      current=buildEventOutputs(model);
      htmlOut.value=current.html;
      jsonOut.value=`<script type="application/ld+json">\n${current.jsonLd}\n<\/script>`;
      results.hidden=false;
      setStatus('Evento generado. Revisa los datos antes de publicarlo.',false);
      emit('event_builder',{result:'generated',mode:model.allDay?'all_day':'timed'});
    }catch(err){ setStatus(err.message||'No se pudo generar el evento.',true); }
  });

  download.addEventListener('click',()=>{
    if(!current) return;
    const blob=new Blob([current.ics],{type:'text/calendar;charset=utf-8'});
    const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=current.filename; document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1200);
    emit('event_builder_ics',{result:'download'});
  });

  root.querySelectorAll('[data-copy-target]').forEach(btn=>btn.addEventListener('click',async()=>{
    const target=root.querySelector(btn.dataset.copyTarget); if(!target?.value) return;
    await navigator.clipboard.writeText(target.value); btn.textContent='Copiado'; setTimeout(()=>btn.textContent='Copiar',1200);
  }));

  function toggleMode(){ timed.hidden=allDay.checked; dated.hidden=!allDay.checked; }
  function setStatus(msg,error){status.textContent=msg;status.dataset.state=error?'error':'normal';}
}

function modelFromForm(form){ const d=new FormData(form); return {
  name:d.get('name'),url:d.get('url'),description:d.get('description'),venueName:d.get('venueName'),streetAddress:d.get('streetAddress'),addressLocality:d.get('addressLocality'),postalCode:d.get('postalCode'),addressRegion:d.get('addressRegion'),addressCountry:d.get('addressCountry'),imageUrl:d.get('imageUrl'),organizerName:d.get('organizerName'),organizerUrl:d.get('organizerUrl'),allDay:d.get('allDay')==='on',startDate:d.get('startDate'),endDate:d.get('endDate'),startDateTime:d.get('startDateTime'),endDateTime:d.get('endDateTime'),utcOffset:d.get('utcOffset'),confirmed:d.get('confirmed')==='on'
};}
function emit(event,detail){document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event,...detail}}));}
