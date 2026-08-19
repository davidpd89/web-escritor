const HTTPS_RE = /^https:\/\//i;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const DATETIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

export const MODES = {
  profile: { label: 'Perfil de autor', schema: 'ProfilePage + Person', googleFeature: 'Profile page' },
  book: { label: 'Libro', schema: 'Book', googleFeature: null },
  article: { label: 'Artículo', schema: 'Article', googleFeature: 'Article' },
  event: { label: 'Evento', schema: 'Event', googleFeature: 'Event' },
};

const clean = v => String(v ?? '').trim();
const compact = obj => Object.fromEntries(Object.entries(obj).filter(([,v]) => v !== '' && v !== null && v !== undefined && !(Array.isArray(v) && v.length === 0)));
const sameAs = value => clean(value).split(/[\n,]+/).map(s=>s.trim()).filter(Boolean);

export function safeJsonLd(data) {
  return JSON.stringify(data, null, 2)
    .replace(/</g, '\\u003C')
    .replace(/>/g, '\\u003E')
    .replace(/&/g, '\\u0026');
}

export function buildJsonLd(mode, data = {}) {
  if (!MODES[mode]) throw new Error('Modo no soportado');
  const d = Object.fromEntries(Object.entries(data).map(([k,v]) => [k, typeof v === 'string' ? clean(v) : v]));

  if (mode === 'profile') {
    const personId = d.personId || (d.url ? `${d.url.replace(/\/$/, '')}/#person` : '');
    const person = compact({
      '@type': 'Person', '@id': personId, name: d.name, url: d.url,
      description: d.description,
      image: d.image,
      sameAs: sameAs(d.sameAs),
    });
    return compact({
      '@context': 'https://schema.org', '@type': 'ProfilePage',
      '@id': d.pageId || d.url, url: d.url, name: d.pageName || d.name,
      mainEntity: person,
    });
  }

  if (mode === 'book') {
    const author = d.authorName ? compact({ '@type': 'Person', name: d.authorName, url: d.authorUrl }) : undefined;
    const publisher = d.publisher ? { '@type': 'Organization', name: d.publisher } : undefined;
    return compact({
      '@context': 'https://schema.org', '@type': 'Book', '@id': d.id || d.url,
      name: d.name, url: d.url, description: d.description, image: d.image,
      isbn: d.isbn, numberOfPages: d.pages ? Number(d.pages) : undefined,
      datePublished: d.datePublished, inLanguage: d.language || 'es',
      genre: d.genre, author, publisher,
    });
  }

  if (mode === 'article') {
    const author = d.authorName ? compact({ '@type': 'Person', name: d.authorName, url: d.authorUrl }) : undefined;
    return compact({
      '@context': 'https://schema.org', '@type': 'Article', '@id': d.id || d.url,
      mainEntityOfPage: d.url, url: d.url, headline: d.headline,
      description: d.description, image: d.image, datePublished: d.datePublished,
      dateModified: d.dateModified, inLanguage: d.language || 'es', author,
    });
  }

  const location = d.locationName ? compact({
    '@type': 'Place', name: d.locationName,
    address: d.address ? { '@type': 'PostalAddress', streetAddress: d.address, addressLocality: d.city, addressCountry: d.country || 'ES' } : undefined,
  }) : undefined;
  const organizer = d.organizerName ? compact({ '@type': 'Organization', name: d.organizerName, url: d.organizerUrl }) : undefined;
  return compact({
    '@context': 'https://schema.org', '@type': 'Event', '@id': d.id || d.url,
    name: d.name, url: d.url, description: d.description, image: d.image,
    startDate: d.startDate, endDate: d.endDate, eventStatus: d.eventStatus || 'https://schema.org/EventScheduled',
    eventAttendanceMode: d.attendanceMode || 'https://schema.org/OfflineEventAttendanceMode',
    location, organizer,
  });
}

export function validateInput(mode, data = {}) {
  const errors = [], warnings = [], info = [];
  const req = (key, label) => { if (!clean(data[key])) errors.push(`Falta ${label}.`); };
  const https = (key, label, required=false) => {
    const v = clean(data[key]); if (required && !v) errors.push(`Falta ${label}.`);
    else if (v && !HTTPS_RE.test(v)) errors.push(`${label} debe usar https://.`);
  };

  if (mode === 'profile') {
    req('name','el nombre del autor'); https('url','la URL canónica del perfil',true);
    if (!clean(data.description)) warnings.push('Añade una descripción solo si esa información también es visible en la página.');
    for (const url of sameAs(data.sameAs)) if (!HTTPS_RE.test(url)) errors.push(`sameAs no es HTTPS: ${url}`);
    info.push('Google documenta ProfilePage; el Person va como mainEntity del perfil.');
  } else if (mode === 'book') {
    req('name','el título'); https('url','la URL canónica del libro',true); req('authorName','el autor');
    if (data.pages && (!Number.isInteger(Number(data.pages)) || Number(data.pages) <= 0)) errors.push('El número de páginas debe ser un entero positivo.');
    if (data.datePublished && !DATE_RE.test(clean(data.datePublished))) errors.push('La fecha de publicación debe usar AAAA-MM-DD.');
    info.push('Book es un tipo Schema.org, pero Google no lo lista actualmente como rich result dedicado en su galería de datos estructurados.');
    warnings.push('No añadas precio, disponibilidad u Offer si no existe una oferta real y visible en la página.');
  } else if (mode === 'article') {
    req('headline','el titular'); https('url','la URL canónica del artículo',true); req('authorName','el autor'); req('datePublished','la fecha de publicación');
    if (data.datePublished && !DATE_RE.test(clean(data.datePublished))) errors.push('datePublished debe usar AAAA-MM-DD.');
    if (data.dateModified && !DATE_RE.test(clean(data.dateModified))) errors.push('dateModified debe usar AAAA-MM-DD.');
    info.push('Article está en la galería de funciones de datos estructurados de Google.');
  } else if (mode === 'event') {
    req('name','el nombre del evento'); https('url','la URL canónica del evento',true); req('startDate','la fecha/hora de inicio');
    if (data.startDate && !DATETIME_RE.test(clean(data.startDate))) errors.push('startDate debe incluir fecha y hora en formato ISO local.');
    if (data.endDate && !DATETIME_RE.test(clean(data.endDate))) errors.push('endDate debe incluir fecha y hora en formato ISO local.');
    if (data.startDate && data.endDate && new Date(data.endDate) < new Date(data.startDate)) errors.push('endDate no puede ser anterior a startDate.');
    if (data.attendanceMode?.includes('Offline') && !clean(data.locationName)) warnings.push('Un evento presencial debería indicar un lugar visible y real.');
    info.push('Event está en la galería de funciones de datos estructurados de Google, sujeto a sus directrices específicas.');
  }

  if (clean(data.image) && !HTTPS_RE.test(clean(data.image))) errors.push('La imagen debe usar una URL HTTPS absoluta.');
  warnings.push('El marcado debe describir contenido visible en la página; no uses el JSON-LD para añadir hechos que el lector no puede comprobar allí.');
  warnings.push('Pasar estas comprobaciones no garantiza un rich result ni sustituye Rich Results Test/URL Inspection.');
  return { valid: errors.length === 0, errors, warnings, info };
}

export function scriptTag(jsonLd) {
  return `<script type="application/ld+json">\n${safeJsonLd(jsonLd)}\n<\/script>`;
}
