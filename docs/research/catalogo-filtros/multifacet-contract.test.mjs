import test from 'node:test';
import assert from 'node:assert/strict';
import { parseHash, writeHash, matchesMulti, availableOptions } from './multifacet-contract.mjs';

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
