// book-page-audit-rules.js
// Extensión modular para el auditor de web de escritor.
// Analiza una página individual de libro a partir del HTML ya descargado por el Worker.
// No hace fetch, no puntúa SEO y no convierte señales opcionales en requisitos.

const clean = (s='') => String(s)
  .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
  .replace(/<[^>]+>/g, ' ')
  .replace(/&nbsp;/gi, ' ')
  .replace(/&amp;/gi, '&')
  .replace(/&quot;/gi, '"')
  .replace(/&#39;|&apos;/gi, "'")
  .replace(/\s+/g, ' ')
  .trim();

const attr = (tag, name) => {
  const re = new RegExp(`\\b${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, 'i');
  const m = String(tag).match(re);
  return m ? (m[1] ?? m[2] ?? m[3] ?? '') : '';
};

const normalize = (s='') => String(s)
  .normalize('NFD').replace(/\p{M}/gu, '')
  .toLowerCase().replace(/\s+/g, ' ').trim();

const hasAny = (haystack, needles) => {
  const h = normalize(haystack);
  return needles.some(n => h.includes(normalize(n)));
};

const getMeta = (html, key, property=false) => {
  const tags = String(html).match(/<meta\b[^>]*>/gi) || [];
  for (const tag of tags) {
    const k = attr(tag, property ? 'property' : 'name');
    if (normalize(k) === normalize(key)) return attr(tag, 'content');
  }
  return '';
};

const getLinks = (html) => {
  const out = [];
  const re = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(String(html)))) {
    out.push({ href: attr(`<a ${m[1]}>`, 'href'), text: clean(m[2]) });
  }
  return out;
};

const getImages = (html) => {
  return (String(html).match(/<img\b[^>]*>/gi) || []).map(tag => ({
    src: attr(tag, 'src'),
    alt: attr(tag, 'alt'),
    width: attr(tag, 'width'),
    height: attr(tag, 'height'),
  }));
};

const collectJsonLd = (html) => {
  const blocks = [];
  const re = /<script\b[^>]*type\s*=\s*(?:"application\/ld\+json"|'application\/ld\+json')[^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(String(html)))) {
    try { blocks.push(JSON.parse(m[1].trim())); } catch { /* base auditor can report parse errors */ }
  }
  return blocks;
};

const walk = (value, fn) => {
  if (!value || typeof value !== 'object') return;
  fn(value);
  if (Array.isArray(value)) value.forEach(v => walk(v, fn));
  else Object.values(value).forEach(v => walk(v, fn));
};

const bookEntities = (jsonLd) => {
  const books = [];
  jsonLd.forEach(root => walk(root, node => {
    const t = node?.['@type'];
    const types = Array.isArray(t) ? t : [t];
    if (types.filter(Boolean).some(x => normalize(x) === 'book')) books.push(node);
  }));
  return books;
};

const digits = s => String(s || '').replace(/\D/g, '');
const isbn13FromText = (text) => {
  const candidates = String(text).match(/(?:97[89][\s-]?)?(?:\d[\s-]?){9,12}\d/g) || [];
  for (const c of candidates) {
    const d = digits(c);
    if (d.length === 13 && /^97[89]/.test(d)) return d;
  }
  return '';
};

const finding = (id, status, title, detail, evidence='') => ({
  id, status, title, detail, ...(evidence ? { evidence } : {})
});

export function auditBookPageHtml(html, options={}) {
  const source = String(html || '');
  const visible = clean(source);
  const links = getLinks(source);
  const images = getImages(source);
  const jsonLd = collectJsonLd(source);
  const books = bookEntities(jsonLd);
  const primaryBook = books[0] || null;

  const h1 = clean((source.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i) || [,''])[1]);
  const titleTag = clean((source.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || [,''])[1]);
  const metaDescription = getMeta(source, 'description');
  const ogImage = getMeta(source, 'og:image', true);
  const expectedTitle = String(options.expectedTitle || primaryBook?.name || h1 || '').trim();

  const purchaseTerms = ['comprar','compra','reservar','reserva','preventa','pre-order','preorder',
    'amazon','casa del libro','fnac','kobo','apple books','google play','todos los formatos'];
  const excerptTerms = ['fragmento','leer muestra','muestra gratuita','primer capitulo','primer capítulo',
    'leer un capitulo','leer un capítulo','sample','extracto'];
  const pressTerms = ['prensa','press kit','media kit','kit de prensa','descargar portada','material de prensa'];
  const clubTerms = ['club de lectura','guia de lectura','guía de lectura','preguntas para debatir','book club'];
  const seriesTerms = ['serie','saga','orden de lectura','reading order','libro 1','libro 2','volumen'];
  const rightsTerms = ['derechos de uso','uso de imagen','creditos','créditos','licencia','copyright'];
  const availabilityTerms = ['ya disponible','disponible','preventa','preventas','reserva','reservar','proximamente',
    'próximamente','a la venta','publicacion','publicación'];

  const purchaseLinks = links.filter(l => hasAny(`${l.text} ${l.href}`, purchaseTerms));
  const excerptLinks = links.filter(l => hasAny(`${l.text} ${l.href}`, excerptTerms));
  const pressLinks = links.filter(l => hasAny(`${l.text} ${l.href}`, pressTerms));

  const textIsbn = isbn13FromText(visible);
  const schemaIsbn = digits(primaryBook?.isbn || '');
  const schemaPublisher = typeof primaryBook?.publisher === 'string'
    ? primaryBook.publisher : primaryBook?.publisher?.name || '';
  const schemaDate = primaryBook?.datePublished || '';
  const schemaFormat = primaryBook?.bookFormat || '';
  const schemaPages = primaryBook?.numberOfPages || '';
  const schemaImage = typeof primaryBook?.image === 'string'
    ? primaryBook.image : primaryBook?.image?.url || '';

  const coverLikely = Boolean(
    ogImage || schemaImage ||
    images.find(img => expectedTitle && hasAny(`${img.alt} ${img.src}`, [expectedTitle])) ||
    images.find(img => hasAny(`${img.alt} ${img.src}`, ['portada','cover']))
  );

  const descriptionLikely = Boolean(
    metaDescription.length >= 80 ||
    (primaryBook?.description && String(primaryBook.description).length >= 80) ||
    visible.length >= 600
  );

  const titleVisible = Boolean(h1 && (!expectedTitle || hasAny(h1, [expectedTitle]) || hasAny(expectedTitle, [h1])));
  const authorVisible = hasAny(visible.slice(0, 3500), ['autor','autora']) || Boolean(primaryBook?.author);
  const availabilityVisible = hasAny(visible, availabilityTerms);
  const excerptVisible = hasAny(visible, excerptTerms) || excerptLinks.length > 0;
  const pressVisible = hasAny(visible, pressTerms) || pressLinks.length > 0;
  const clubVisible = hasAny(visible, clubTerms);
  const seriesVisible = hasAny(visible, seriesTerms);
  const rightsVisible = hasAny(visible, rightsTerms);

  const factsVisible = {
    isbn: Boolean(textIsbn),
    publisher: hasAny(visible, ['editorial','publicado por','publicada por']) || Boolean(schemaPublisher),
    date: hasAny(visible, ['fecha de publicación','fecha de publicacion','publicado','publicada']) || Boolean(schemaDate),
    format: hasAny(visible, ['tapa blanda','tapa dura','ebook','e-book','audiolibro','formato']) || Boolean(schemaFormat),
    pages: hasAny(visible, ['páginas','paginas']) || Boolean(schemaPages),
  };

  const core = [
    titleVisible
      ? finding('book_title','ok','Título visible','La página tiene un H1 coherente con el libro.',h1)
      : finding('book_title','review','Título visible','No se ha podido confirmar un H1 que identifique claramente el libro.'),
    authorVisible
      ? finding('book_author','ok','Autoría visible','Se detecta una señal de autoría en contenido o datos estructurados.')
      : finding('book_author','review','Autoría visible','Conviene que el lector identifique claramente quién firma el libro.'),
    coverLikely
      ? finding('book_cover','ok','Portada','Se detecta una imagen de portada o una señal equivalente.')
      : finding('book_cover','review','Portada','No se ha podido identificar una portada clara.'),
    descriptionLikely
      ? finding('book_description','ok','Descripción','Hay suficiente contenido descriptivo o una descripción estructurada.')
      : finding('book_description','review','Descripción','La página parece demasiado escueta para explicar de qué trata el libro.'),
    availabilityVisible
      ? finding('book_availability','ok','Estado de disponibilidad','Se detecta si el libro está disponible, en preventa o próximo.')
      : finding('book_availability','review','Estado de disponibilidad','No se ha detectado una señal clara de disponibilidad o lanzamiento.'),
    purchaseLinks.length
      ? finding('book_purchase','ok','Acción de compra','Se detecta al menos una salida de compra/reserva.', `${purchaseLinks.length} enlace(s)`)
      : finding('book_purchase','review','Acción de compra','No se ha detectado un enlace claro para comprar, reservar o continuar hacia la compra.'),
  ];

  const metadata = [
    factsVisible.isbn
      ? finding('book_isbn','ok','ISBN','Se detecta ISBN-13 visible o estructurado.', textIsbn || schemaIsbn)
      : finding('book_isbn','info','ISBN','No se detecta ISBN-13. Añádelo solo si la edición publicada dispone de uno.'),
    factsVisible.publisher
      ? finding('book_publisher','ok','Editorial','Se detecta editorial o publisher.')
      : finding('book_publisher','info','Editorial','No se detecta editorial. No debe inventarse si no existe o no está confirmada.'),
    factsVisible.date
      ? finding('book_date','ok','Fecha de publicación','Se detecta una fecha/señal de publicación.')
      : finding('book_date','info','Fecha de publicación','No se detecta fecha. Solo debe publicarse cuando esté confirmada.'),
    factsVisible.format
      ? finding('book_format','ok','Formato','Se detecta información de formato/edición.')
      : finding('book_format','optional','Formato','Puede ser útil cuando existen varias ediciones o formatos.'),
    factsVisible.pages
      ? finding('book_pages','ok','Páginas','Se detecta número de páginas.')
      : finding('book_pages','optional','Páginas','Dato útil pero no imprescindible para todas las páginas de autor.'),
  ];

  const enriched = [
    excerptVisible
      ? finding('book_excerpt','ok','Muestra o fragmento','Se detecta una muestra, capítulo o fragmento.')
      : finding('book_excerpt','optional','Muestra o fragmento','Puede reducir incertidumbre del lector cuando exista un fragmento publicable.'),
    pressVisible
      ? finding('book_press','ok','Prensa / media','Se detecta material para prensa o medios.')
      : finding('book_press','optional','Prensa / media','Útil si se busca cobertura, entrevistas o reseñas.'),
    clubVisible
      ? finding('book_club','ok','Clubes de lectura','Se detecta guía o material para clubes.')
      : finding('book_club','optional','Clubes de lectura','Añadir solo si el libro y la estrategia lo justifican.'),
    seriesVisible
      ? finding('book_series','ok','Serie / orden','Se detecta contexto de serie, saga u orden de lectura.')
      : finding('book_series','optional','Serie / orden','No aplica a libros independientes.'),
    rightsVisible
      ? finding('book_asset_rights','ok','Uso de assets','Se detectan créditos, licencia o derechos de uso.')
      : finding('book_asset_rights','optional','Uso de assets','Recomendable si se ofrecen portadas/fotos descargables a prensa o terceros.'),
  ];

  const structured = books.length
    ? finding('book_schema','ok','Book JSON-LD',`Se detectan ${books.length} entidad(es) Book. Deben coincidir con lo visible.`)
    : finding('book_schema','info','Book JSON-LD','No se detecta Book JSON-LD. Schema.org puede describir el libro, pero no debe presentarse como requisito de ranking.');

  const consistency = [];
  if (schemaIsbn && textIsbn && schemaIsbn !== textIsbn) {
    consistency.push(finding('book_isbn_mismatch','review','ISBN inconsistente',
      'El ISBN visible no coincide con el ISBN del primer Book JSON-LD.',
      `${textIsbn} ≠ ${schemaIsbn}`));
  }
  if (primaryBook?.name && h1 && !hasAny(h1, [primaryBook.name]) && !hasAny(primaryBook.name, [h1])) {
    consistency.push(finding('book_title_mismatch','review','Título inconsistente',
      'El nombre del Book JSON-LD no parece coincidir con el H1 visible.',
      `${primaryBook.name} ↔ ${h1}`));
  }

  return {
    mode: 'book-page',
    url: String(options.url || ''),
    detectedTitle: expectedTitle || titleTag,
    findings: { core, metadata, enriched, structured: [structured], consistency },
    evidence: {
      h1, titleTag, metaDescriptionLength: metaDescription.length,
      imageCount: images.length, purchaseLinkCount: purchaseLinks.length,
      excerptLinkCount: excerptLinks.length, bookEntityCount: books.length,
    }
  };
}
