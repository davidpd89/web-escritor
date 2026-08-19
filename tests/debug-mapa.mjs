import { normalizeProject } from '../assets/mapa-personajes-core.js';
const project = normalizeProject({characters:[{name:'Noa'},{name:'Brais'},{name:'Cibrán'}],relations:[{from:'noa',to:'brais',type:'alianza',label:'confianza'},{from:'noa',to:'cibran',type:'rivalidad'}]});
console.log(JSON.stringify(project, null, 2));
