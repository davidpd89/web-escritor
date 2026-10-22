import test from 'node:test';
import assert from 'node:assert/strict';
import { parseHash, writeHash, matchesMulti, availableOptions, sanitizeFacetSelections, matchingOffersMulti } from './multifacet-contract.mjs';

// Four real titles and facets taken from recomendaciones/index.html (main, 22-10-2026).
const books = [
  { title: 'Barbacoa', group: 'cocina', categories: ['cocina'], formats: ['tapa-dura'] },
  { title: 'Coraline', group: 'infantil', categories: ['terror', 'fantasia-juvenil', 'fantasia', 'aventuras'], formats: ['tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro'] },
  { title: 'Las Pruebas del Tarot', group: 'novela', categories: ['fantasia'], formats: ['tapa-dura'] },
  { title: 'Otros mundos (El Talismán 3)', group: 'novela', categories: ['terror', 'fantasia', 'misterio-y-thriller'], formats: ['tapa-dura'] }
];
const selected = extra => ({ ...parseHash(''), ...extra });

test('OR: dos formatos incluyen cualquier libro con al menos uno', () => {
  assert.equal(books.filter(b => matchesMulti(b, selected({formato:['tapa-blanda','tapa-dura']}))).length, 4);
});
test('AND: género Fantasía restringe cualquiera de los formatos', () => {
  const result = books.filter(b => matchesMulti(b, selected({formato:['tapa-blanda','tapa-dura'],genero:['fantasia']})));
  assert.deepEqual(result.map(b=>b.title), ['Coraline','Las Pruebas del Tarot','Otros mundos (El Talismán 3)']);
});
test('OR: dos categorías del mismo grupo no fuerzan coincidencia simultánea', () => {
  assert.equal(books.filter(b=>matchesMulti(b, selected({genero:['fantasia','cocina']}))).length, 4);
});
test('AND: géneros elegidos más tipo Cocina limita a un libro', () => {
  const result=books.filter(b=>matchesMulti(b, selected({grupo:'cocina',genero:['fantasia','cocina']})));
  assert.deepEqual(result.map(b=>b.title),['Barbacoa']);
});
test('lista dependiente: cuenta género sin restringirse a su propia elección', () => {
  const options=availableOptions(books,selected({grupo:'novela',genero:['fantasia']}),'genero',[
    {value:'fantasia',label:'Fantasía'},{value:'terror',label:'Terror'},{value:'cocina',label:'Cocina'}]);
  assert.deepEqual(options.map(o=>[o.value,o.count]),[['fantasia',2],['terror',1]]);
});
test('opción activa imposible conservada para quitarla',()=>{
  const options=availableOptions(books,selected({grupo:'cocina',genero:['fantasia']}),'genero',[
    {value:'fantasia',label:'Fantasía'},{value:'cocina',label:'Cocina'}]);
  assert.deepEqual(options.map(o=>[o.value,o.count,o.selected]),[['fantasia',0,true],['cocina',1,false]]);
});
test('hash antiguo de un valor se restaura como un array',()=>{
  const state=parseHash('#genero=fantasia&grupo=novela');
  assert.deepEqual(state.genero,['fantasia']); assert.equal(state.grupo,'novela');
});
test('hash nuevo de múltiples valores conserva todos y página',()=>{
  const state=parseHash('#formato=tapa-blanda&formato=tapa-dura&genero=fantasia&genero=terror&pagina=2');
  assert.deepEqual(state.formato,['tapa-blanda','tapa-dura']);
  assert.deepEqual(parseHash(writeHash(state)).genero,['fantasia','terror']);
  assert.equal(parseHash(writeHash(state)).pagina,2);
});
test('desduplicación segura de filtros URL',()=>{
  assert.deepEqual(parseHash('#genero=fantasia&genero=fantasia').genero,['fantasia']);
});
test('título buscado y múltiples formatos no crean falsos positivos',()=>{
  const state=selected({q:'Coraline',formato:['tapa-blanda','tapa-dura']});
  assert.deepEqual(books.filter(b=>matchesMulti(b,state)).map(b=>b.title),['Coraline']);
});

test('los filtros anteriores de extensión, novedades, precios, fechas y valoración sobreviven al cambio de formato',()=>{
  const old='#genero=fantasia&paginas=breve&novedad=30&precio_max=20&precio_min=5&desde=2024-01-01&hasta=2026-12-31&descuento=10&valoracion=4';
  const state=parseHash(old);
  state.formato=['tapa-blanda','tapa-dura'];
  const restored=parseHash(writeHash(state));
  for (const key of ['paginas','novedad','precio_max','precio_min','desde','hasta','descuento','valoracion']) {
    assert.equal(restored[key],state[key],key);
  }
  assert.deepEqual(restored.formato,['tapa-blanda','tapa-dura']);
});
test('la URL elimina solo parámetros vacíos y conserva búsqueda, orden y grupo',()=>{
  const state=parseHash('#q=Coraline&grupo=infantil&orden=titulo&genero=fantasia&paginas=breve&valoracion=');
  state.genero=[];
  assert.deepEqual(parseHash(writeHash(state)),{...state,valoracion:''});
  assert(!writeHash(state).includes('valoracion='));
});

test('una faceta eliminada de la taxonomía no bloquea el catálogo sin control visible', () => {
  const old = parseHash('#formato=tapa-dura&formato=desconocido&genero=no-existe');
  const master = {
    formato: [{ value: 'tapa-dura', label: 'Tapa dura' }],
    genero: [{ value: 'fantasia', label: 'Fantasía' }]
  };
  const clean = sanitizeFacetSelections(old, master);
  assert.deepEqual(clean.formato, ['tapa-dura']);
  assert.deepEqual(clean.genero, []);
  assert(!writeHash(clean).includes('desconocido'));
  assert(!writeHash(clean).includes('no-existe'));
});

test('selección conocida que ahora devuelve 0 libros NO se elimina por sanear URL', () => {
  const state = selected({grupo:'cocina', genero:['fantasia']});
  const clean = sanitizeFacetSelections(state, { genero: [{value:'fantasia',label:'Fantasía'}] });
  assert.deepEqual(clean.genero, ['fantasia']);
  assert.deepEqual(books.filter(book => matchesMulti(book, clean)), []);
  assert.deepEqual(state.genero, ['fantasia'], 'sin mutar el estado original');
});

test('sanear una faceta mantiene valores, búsqueda y filtros escalares no tratados', () => {
  const state = selected({ q:'Coraline', paginas:'breve', genero:['fantasia'], formato:['ebook'] });
  const cleaned = sanitizeFacetSelections(state, { formato:[{value:'ebook',label:'Ebook'}] });
  assert.deepEqual(cleaned.genero,['fantasia']);
  assert.equal(cleaned.paginas,'breve');
  assert.equal(cleaned.q,'Coraline');
});

test('categoría activa con 0 libros se conserva, la categoría eliminada no', () => {
  const masters = { genero: [
    { value:'fantasia',label:'Fantasía' },
    { value:'romantasy',label:'Romantasy' }
  ] };
  const state = selected({genero:['romantasy','eliminada']});
  const cleaned = sanitizeFacetSelections(state,masters);
  assert.deepEqual(cleaned.genero,['romantasy']);
  const options = availableOptions(books,cleaned,'genero',masters.genero);
  assert.deepEqual(options.map(o=>[o.value,o.count,o.selected]),[
    ['fantasia',3,false],['romantasy',0,true]
  ]);
});

const syntheticVerifiedOffers = [
  {formato:'tapa-blanda',precio_centimos:950,precio_referencia_centimos:1500},
  {formato:'tapa-dura',precio_centimos:2590,precio_referencia_centimos:2700},
  {formato:'ebook',precio_centimos:690}
];

test('precio máximo y formato deben cumplirse en una misma oferta, nunca en dos distintas',()=>{
  const wanted={formato:['tapa-dura'],precio_max:'10'};
  assert.deepEqual(matchingOffersMulti(syntheticVerifiedOffers,wanted),[]);
});

test('OR entre formatos sí admite la tapa blanda cuando está dentro del presupuesto',()=>{
  const wanted={formato:['tapa-blanda','tapa-dura'],precio_max:'10'};
  assert.deepEqual(matchingOffersMulti(syntheticVerifiedOffers,wanted).map(o=>o.formato),['tapa-blanda']);
});

test('rango de precios y descuento se evalúan juntos sobre cada formato elegible',()=>{
  const wanted={formato:['tapa-blanda','tapa-dura'],precio_min:'9',precio_max:'27',descuento:'30'};
  assert.deepEqual(matchingOffersMulti(syntheticVerifiedOffers,wanted).map(o=>o.formato),['tapa-blanda']);
});

test('formato escalar antiguo, sin formato y sin ofertas preservan semántica',()=>{
  assert.deepEqual(matchingOffersMulti(syntheticVerifiedOffers,{formato:'tapa-dura'}).map(o=>o.formato),['tapa-dura']);
  assert.equal(matchingOffersMulti(syntheticVerifiedOffers,{}).length,3);
  assert.deepEqual(matchingOffersMulti([],{formato:['tapa-blanda','tapa-dura'],precio_max:'30'}),[]);
});

test('mínimo por formato solo usa ofertas de ese formato, útil para ordenar precios',()=>{
  const accepted=matchingOffersMulti(syntheticVerifiedOffers,{formato:['tapa-dura','ebook']});
  assert.equal(Math.min(...accepted.map(o=>o.precio_centimos)),690);
  assert.equal(Math.min(...matchingOffersMulti(syntheticVerifiedOffers,{formato:['tapa-dura']}).map(o=>o.precio_centimos)),2590);
});


test('quiz heredado: género y formato escalares coinciden sin lanzar TypeError',()=>{
  const v={genero:'fantasia',formato:'tapa-dura'};
  assert.deepEqual(books.filter(b=>matchesMulti(b,v)).map(b=>b.title),[
    'Coraline','Las Pruebas del Tarot','Otros mundos (El Talismán 3)'
  ]);
});

test('quiz heredado: valor singular de temática no genera coincidencias parciales',()=>{
  const v={genero:'fantasia-juvenil'};
  assert.deepEqual(books.filter(b=>matchesMulti(b,v)).map(b=>b.title),['Coraline']);
});

test('facetas heredadas: selección escalar solo marca valor exacto, no prefijo',()=>{
  const values=availableOptions(books,{genero:'fantasia-juvenil'},'genero',[
    {value:'fantasia',label:'Fantasía'},
    {value:'fantasia-juvenil',label:'Fantasía juvenil'}
  ]);
  assert.deepEqual(values.map(o=>[o.value,o.selected]),[
    ['fantasia',false],['fantasia-juvenil',true]
  ]);
});


test('URL del quiz: writeHash acepta escalares sin separarlos en caracteres',()=>{
  const url=writeHash({genero:'fantasia',formato:'tapa-dura',q:'Coraline'});
  assert.deepEqual(new URLSearchParams(url.slice(1)).getAll('genero'),['fantasia']);
  assert.deepEqual(new URLSearchParams(url.slice(1)).getAll('formato'),['tapa-dura']);
  assert.deepEqual(parseHash(url).formato,['tapa-dura']);
});
