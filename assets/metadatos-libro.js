function escapeAttr(value) {
  return String(value ?? '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function normalizeHandle(value) {
  const v = String(value || '').trim();
  if (!v) return '';
  return v.startsWith('@') ? v : `@${v}`;
}

export function httpsUrl(value) {
  const trimmed = String(value || '').trim();
  try {
    const u = new URL(trimmed);
    if (u.protocol !== 'https:') return '';
    if (/%[0-9a-f]{2}/i.test(u.hostname)) return '';
    return u.href;
  } catch {
    return '';
  }
}

export function buildMetaTags(v = {}) {
  const canonical = httpsUrl(v.url);
  const image = httpsUrl(v.image);
  const authorUrl = httpsUrl(v.authorUrl);
  const title = `${v.book || ''}${v.author ? ` — ${v.author}` : ''}${v.site ? ` | ${v.site}` : ''}`;
  const socialTitle = `${v.book || ''}${v.author ? ` — ${v.author}` : ''}`;
  const lines = [
    `<title>${escapeAttr(title)}</title>`,
    `<meta name="description" content="${escapeAttr(v.description)}">`,
    canonical ? `<link rel="canonical" href="${escapeAttr(canonical)}">` : '',
    '',
    '<meta property="og:type" content="book">',
    `<meta property="og:title" content="${escapeAttr(socialTitle)}">`,
    `<meta property="og:description" content="${escapeAttr(v.description)}">`,
    canonical ? `<meta property="og:url" content="${escapeAttr(canonical)}">` : '',
    v.site ? `<meta property="og:site_name" content="${escapeAttr(v.site)}">` : '',
    image ? `<meta property="og:image" content="${escapeAttr(image)}">` : '',
    image && v.imageAlt ? `<meta property="og:image:alt" content="${escapeAttr(v.imageAlt)}">` : '',
    authorUrl ? `<meta property="book:author" content="${escapeAttr(authorUrl)}">` : '',
    v.isbn ? `<meta property="book:isbn" content="${escapeAttr(String(v.isbn).replace(/[\s-]/g, ''))}">` : '',
    v.releaseDate ? `<meta property="book:release_date" content="${escapeAttr(v.releaseDate)}">` : '',
    '',
    '<meta name="twitter:card" content="summary_large_image">',
    `<meta name="twitter:title" content="${escapeAttr(socialTitle)}">`,
    `<meta name="twitter:description" content="${escapeAttr(v.description)}">`,
    image ? `<meta name="twitter:image" content="${escapeAttr(image)}">` : '',
    image && v.imageAlt ? `<meta name="twitter:image:alt" content="${escapeAttr(v.imageAlt)}">` : '',
    v.xSite ? `<meta name="twitter:site" content="${escapeAttr(normalizeHandle(v.xSite))}">` : '',
  ].filter((line, i, arr) => line !== '' || (i && arr[i - 1] !== '')).join('\n');
  return { canonical, image, title, socialTitle, lines };
}

export function validateMetaTags(v = {}, built) {
  const b = built || buildMetaTags(v);
  const items = [];
  if (!v.book) items.push('Añade el título del libro.');
  if (!v.description) items.push('Añade una descripción específica de esta página.');
  if (v.url && !b.canonical) items.push('La URL canónica debe ser una URL HTTPS válida.');
  if (!v.url) items.push('Falta la URL canónica.');
  if (v.image && !b.image) items.push('La imagen social debe usar una URL HTTPS válida.');
  if (!v.image) items.push('Falta una imagen social.');
  if (v.image && !v.imageAlt) items.push('Añade texto alternativo para la imagen social.');
  if (v.authorUrl && !httpsUrl(v.authorUrl)) items.push('La URL del perfil del autor debe ser una URL HTTPS válida.');
  if ((v.description || '').length > 180) items.push('La descripción es larga. No hay un límite universal de snippet, pero conviene revisar que la idea principal aparezca pronto.');
  if (b.socialTitle.length > 90) items.push('El título social es largo y puede truncarse en algunas interfaces.');
  return items;
}

function setImageReference(slot, src, alt) {
  if (!src) {
    slot.hidden = true;
    slot.textContent = '';
    slot.removeAttribute('aria-label');
    return;
  }
  slot.hidden = false;
  slot.textContent = `Imagen indicada · ${src}`;
  const altNote = alt ? ` Texto alternativo: ${alt}.` : '';
  slot.setAttribute('aria-label', `Imagen social indicada: ${src}.${altNote} No se descarga durante esta previsualización.`);
}

export function init() {
  const form = document.querySelector('[data-meta-form]');
  if (!form) return;

  const processor = document.querySelector('[data-publishing-processor]');
  const q = sel => form.querySelector(sel);
  const output = document.querySelector('[data-meta-output]');
  const code = document.querySelector('[data-meta-code]');
  const warnings = document.querySelector('[data-meta-warnings]');
  const googleTitle = document.querySelector('[data-google-title]');
  const googleUrl = document.querySelector('[data-google-url]');
  const googleDesc = document.querySelector('[data-google-desc]');
  const ogTitle = document.querySelector('[data-og-title]');
  const ogDesc = document.querySelector('[data-og-desc]');
  const ogImage = document.querySelector('[data-og-image]');
  const xTitle = document.querySelector('[data-x-title]');
  const xDesc = document.querySelector('[data-x-desc]');
  const xImage = document.querySelector('[data-x-image]');
  const status = document.querySelector('[data-meta-status]');

  const fields = {
    book: q('[name=book]'), author: q('[name=author]'), site: q('[name=site]'), url: q('[name=url]'),
    description: q('[name=description]'), image: q('[name=image]'), imageAlt: q('[name=image_alt]'),
    isbn: q('[name=isbn]'), releaseDate: q('[name=release_date]'), authorUrl: q('[name=author_url]'),
    xSite: q('[name=x_site]'),
  };

  function values() {
    return Object.fromEntries(Object.entries(fields).map(([k, el]) => [k, el?.value.trim() || '']));
  }

  function render() {
    const v = values();
    const built = buildMetaTags(v);
    const issues = validateMetaTags(v, built);
    googleTitle.textContent = built.title || 'Título del libro — Autor | Sitio';
    googleUrl.textContent = built.canonical || 'https://ejemplo.com/libros/mi-libro/';
    googleDesc.textContent = v.description || 'Descripción de la página del libro. Google puede mostrar otro fragmento según la consulta.';
    ogTitle.textContent = built.socialTitle || 'Título del libro — Autor';
    ogDesc.textContent = v.description || 'Descripción social del libro.';
    xTitle.textContent = built.socialTitle || 'Título del libro — Autor';
    xDesc.textContent = v.description || 'Descripción social del libro.';
    setImageReference(ogImage, built.image, v.imageAlt);
    setImageReference(xImage, built.image, v.imageAlt);
    code.textContent = built.lines;
    warnings.replaceChildren(...issues.map(issue => {
      const li = document.createElement('li'); li.textContent = issue; return li;
    }));
    output.hidden = false;
    status.textContent = issues.length ? `Vista generada con ${issues.length} aviso${issues.length === 1 ? '' : 's'}.` : 'Vista generada sin avisos básicos.';
  }

  form.addEventListener('submit', e => { e.preventDefault(); render(); });
  form.addEventListener('input', () => { if (!output.hidden) render(); });

  document.querySelector('[data-copy-meta]')?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(code.textContent || '');
      status.textContent = 'Código copiado al portapapeles.';
    } catch {
      status.textContent = 'No se pudo copiar automáticamente. Selecciona el código manualmente.';
    }
  });

  document.querySelector('[data-meta-sample]')?.addEventListener('click', () => {
    fields.book.value = 'Las manecillas del recuerdo';
    fields.author.value = 'David Porto Díaz';
    fields.site.value = 'David Porto Díaz';
    fields.url.value = 'https://davidportodiaz.com/las-manecillas-del-recuerdo/';
    fields.description.value = 'Novela coral sobre memoria familiar, objetos heredados y las historias que sobreviven al paso del tiempo.';
    fields.image.value = 'https://davidportodiaz.com/assets/las-manecillas-del-recuerdo-social.webp';
    fields.imageAlt.value = 'Portada de Las manecillas del recuerdo, de David Porto Díaz';
    render();
  });

  if (processor) {
    processor.inert = false;
    processor.removeAttribute('inert');
    processor.removeAttribute('aria-disabled');
  }
}

if (typeof document !== 'undefined') init();
