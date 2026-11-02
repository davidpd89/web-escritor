// Buscador de libros para los bots de comunidad (Discord y Telegram).
// Sin dependencias: funciona igual en Node y en un Cloudflare Worker.
// Entrada: el índice de data/bot-books.json y una frase libre en español.

const norm = s => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/(\d)[.,](\d)/g, '$1.$2').replace(/[^a-z0-9€. ]+|\.(?!\d)|(?<!\d)\./g, ' ').replace(/\s+/g, ' ').trim();

// Palabras de la petición → categorías del catálogo.
const SINONIMOS = {
  fantasia: ['fantasia', 'magia', 'dragones', 'hadas', 'brujas', 'fantastico', 'fantastica'],
  romantasy: ['romantasy'],
  romance: ['romantica', 'romantico', 'romance', 'amor', 'enamorarse', 'pareja'],
  'fantasia-oscura': ['oscura', 'dark'],
  terror: ['terror', 'miedo', 'horror', 'sustos', 'escalofriante', 'fantasmas'],
  'misterio-y-thriller': ['thriller', 'suspense', 'intriga', 'policiaca', 'policiaco', 'crimen', 'asesinato', 'detective', 'investigacion', 'misterio'],
  'tema-novela-negra': ['negra'],
  'ciencia-ficcion': ['ciencia ficcion', 'scifi', 'sci fi', 'futuro', 'espacio', 'robots', 'distopia', 'distopico', 'alienigenas'],
  'novela-historica': ['historica', 'historico', 'epoca', 'guerra', 'medieval', 'antigua roma', 'posguerra'],
  historia: ['historia'],
  juvenil: ['juvenil', 'adolescente', 'adolescentes', 'young adult', 'ya'],
  infantil: ['infantil', 'ninos', 'nino', 'nina', 'ninas', 'peques', 'crios', 'hijo', 'hija', 'cuento', 'cuentos'],
  'comic-y-novela-grafica': ['comic', 'comics', 'manga', 'novela grafica', 'tebeo'],
  poesia: ['poesia', 'poemas', 'versos'],
  ensayo: ['ensayo', 'pensar', 'reflexion'],
  filosofia: ['filosofia'],
  'divulgacion-cientifica': ['divulgacion', 'ciencia'],
  cocina: ['cocina', 'recetas', 'cocinar'],
  'nutricion-y-bienestar': ['nutricion', 'salud', 'bienestar', 'dieta'],
  'desarrollo-personal': ['autoayuda', 'desarrollo personal', 'habitos', 'motivacion', 'productividad'],
  'biografias-y-memorias': ['biografia', 'memorias', 'vida real'],
  humor: ['humor', 'gracioso', 'divertido', 'reirme', 'risas', 'comedia'],
  aventuras: ['aventura', 'aventuras', 'viaje', 'exploracion'],
  clasicos: ['clasico', 'clasicos'],
  halloween: ['halloween'],
  navidad: ['navidad', 'navideno'],
  'tema-amistad': ['amistad', 'amigos'],
  'tema-familia': ['familia', 'familiar'],
  'tema-venganza': ['venganza'],
  'tema-superacion-y-duelo': ['duelo', 'superacion', 'perdida'],
  'tema-religion-y-espiritualidad': ['espiritualidad', 'religion', 'espiritual'],
  portales: ['portal', 'portales'],
  'mundos-paralelos': ['mundos paralelos', 'otro mundo'],
};
const FORMATOS = { ebook: ['ebook', 'kindle', 'digital', 'electronico'], audiolibro: ['audiolibro', 'audible', 'escuchar'], 'tapa-dura': ['tapa dura'], 'tapa-blanda': ['tapa blanda', 'bolsillo'] };
const VACIAS = new Set(('a al algo algun alguna alguno busco buscando quiero recomienda recomiendame recomendacion recomendar libro libros novela novelas que trate trata sobre de del el la los las un una unos unas y o con sin para por mi me te se en es son lo como mas muy bueno buena algo tipo estoy tengo hay donde cual sea leer lectura parecido parecida similar ' +
  'euros euro precio barato barata menos max maximo hasta anos nuevo nueva nuevos novedad novedades reciente ultimo ultimos enganche engancha').split(' '));
const DIA_MS = 864e5;

function precioMin(libro, formato) {
  const fs = Object.entries(libro.formatos || {}).filter(([f]) => !formato || f === formato);
  if (!fs.length) return null;
  const [f, x] = fs.reduce((a, b) => (b[1].precio < a[1].precio ? b : a));
  return { formato: f, precio: x.precio, url: x.url };
}

/** Extrae filtros de la frase: categorías, formato, precio máximo, edad, novedad y palabras libres. */
export function interpretar(frase) {
  let t = ' ' + norm(frase) + ' ';
  const categorias = new Set(), pistas = [];
  // Primero las expresiones largas, para que «ciencia ficcion» no active también «ciencia».
  for (const [cat, w] of PARES) if (t.includes(' ' + w + ' ')) { categorias.add(cat); pistas.push(w); t = t.replace(' ' + w + ' ', ' '); }
  let formato = null;
  for (const [f, ws] of Object.entries(FORMATOS)) for (const w of ws) if (t.includes(' ' + w + ' ')) { formato = f; t = t.replace(' ' + w + ' ', ' '); }
  const p = t.match(/(?:menos de|hasta|max(?:imo)?|por debajo de|no mas de)\s*(\d+(?:[.,]\d+)?)\s*(?:€|euros?)?/) || t.match(/(\d+(?:[.,]\d+)?)\s*(?:€|euros?)/);
  const precioMax = p ? Math.round(parseFloat(p[1].replace(',', '.')) * 100) : null;
  const e = t.match(/(\d{1,2})\s*anos/);
  const edad = e ? parseInt(e[1], 10) : null;
  const nuevo = /\b(nuevo|nueva|novedad|novedades|reciente|ultimo|ultimos|acaba de salir)\b/.test(t);
  const libres = t.trim().split(' ').filter(w => w && w.length > 2 && !VACIAS.has(w) && !/^\d/.test(w));
  return { categorias: [...categorias], formato, precioMax, edad, nuevo, libres, pistas };
}

const PARES = Object.entries(SINONIMOS).flatMap(([c, ws]) => ws.map(w => [c, w])).sort((a, b) => b[1].length - a[1].length);
// Público (no género): filtra por edad y suma, pero no basta para que un libro encaje.
const PUBLICO = new Set(['infantil', 'juvenil']);
const raizDe = w => (w.length > 5 ? w.slice(0, -1) : w); // plural y género sencillos

/** Devuelve los mejores libros para la frase, con la razón de cada uno. */
export function buscar(indice, frase, { limite = 3, hoy = new Date() } = {}) {
  const q = interpretar(frase);
  const resultados = [];
  for (const libro of indice.libros) {
    let puntos = 0;
    const razones = [];
    const cats = new Set(libro.categorias);
    const comunes = q.categorias.filter(c => cats.has(c));
    const generos = q.categorias.filter(c => !PUBLICO.has(c));
    if (generos.length ? !generos.some(c => cats.has(c)) : q.categorias.length && !comunes.length) continue;
    puntos += comunes.length * 10;
    const sinopsisN = norm(libro.titulo + ' ' + libro.sinopsis);
    for (const w of q.pistas) if (sinopsisN.includes(raizDe(w))) puntos += 3; // «dragones» también puntúa en el texto
    if (comunes.length) razones.push(comunes.map(c => indice.categorias[c] || c).join(', '));
    const compra = precioMin(libro, q.formato);
    if (q.formato && !compra) continue;
    if (q.precioMax && (!compra || compra.precio > q.precioMax)) continue;
    if (q.edad != null) {
      if (libro.edad_min == null || libro.edad_min > q.edad || (q.edad < 14 && cats.has('adultos'))) continue;
      puntos += 5;
    }
    if (q.libres.length) {
      const tit = norm(libro.titulo), aut = norm(libro.autores.join(' ')), sin = norm(libro.sinopsis), cat = norm(libro.categorias.map(c => indice.categorias[c] || c).join(' '));
      let aciertos = 0;
      for (const w of q.libres) {
        const raiz = raizDe(w);
        if (tit.includes(raiz)) { puntos += 12; aciertos++; }
        else if ((' ' + aut + ' ').includes(' ' + w + ' ')) { puntos += 12; aciertos++; } // autor: palabra exacta
        else if (cat.includes(raiz)) { puntos += 6; aciertos++; }
        else if (sin.includes(raiz)) { puntos += 4; aciertos++; }
      }
      if (!aciertos && !comunes.length) continue;
      if (aciertos) razones.push(`coincide con «${q.libres.join(' ')}»`);
    }
    if (libro.fecha) {
      const dias = (hoy - new Date(libro.fecha)) / DIA_MS;
      if (q.nuevo) { if (dias > 365 || dias < -400) continue; puntos += 5; razones.push('novedad'); }
      else if (dias >= 0 && dias < 180) puntos += 1;
    }
    if (puntos <= 0 && (q.categorias.length || q.libres.length)) continue;
    resultados.push({ libro, puntos, razones, compra });
  }
  resultados.sort((a, b) => b.puntos - a.puntos || (b.libro.fecha || '').localeCompare(a.libro.fecha || ''));
  // Variedad: primero un libro por autor; los repetidos solo si faltan huecos.
  const vistos = new Set(), primero = [], resto = [];
  for (const r of resultados) { const a = r.libro.autores[0] || r.libro.id; (vistos.has(a) ? resto : primero).push(r); vistos.add(a); }
  return { consulta: q, resultados: [...primero, ...resto].slice(0, limite), total: resultados.length };
}

const euros = c => (c / 100).toFixed(2).replace('.', ',') + ' €';
const FORMATO_TXT = { ebook: 'ebook', audiolibro: 'audiolibro', 'tapa-dura': 'tapa dura', 'tapa-blanda': 'tapa blanda' };

/** Texto listo para Discord o Telegram (Markdown sencillo). */
export function formatear({ resultados, total }, frase) {
  if (!resultados.length) return `No he encontrado nada en el catálogo para «${frase}». Prueba con un género (thriller, fantasía, romántica…), un autor o un tema. Catálogo completo: https://davidportodiaz.com/lecturas/`;
  const lineas = resultados.map(({ libro, compra, razones }, i) => {
    const precio = compra ? ` · ${euros(compra.precio)} (${FORMATO_TXT[compra.formato] || compra.formato})` : '';
    const sinopsis = libro.sinopsis.length > 180 ? libro.sinopsis.slice(0, 177).trimEnd() + '…' : libro.sinopsis;
    return `**${i + 1}. ${libro.titulo}** — ${libro.autores.join(', ')}${precio}\n${sinopsis}\n${razones.length ? `_${razones.join(' · ')}_\n` : ''}🛒 ${compra ? compra.url : libro.amazon} · 📖 ${libro.web}`;
  });
  const mas = total > resultados.length ? `\n\nHay ${total - resultados.length} más en https://davidportodiaz.com/lecturas/` : '';
  return lineas.join('\n\n') + mas + '\n\n_Enlaces de afiliado: no te cuestan más y ayudan a mantener la web._';
}
