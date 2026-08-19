export function slugify(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "autor";
}

export function sanitizeFilename(name, fallback = "archivo") {
  const raw = String(name || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "");
  const dot = raw.lastIndexOf(".");
  const ext = dot > 0 ? raw.slice(dot).toLowerCase().replace(/[^.a-z0-9]/g, "") : "";
  const stem = (dot > 0 ? raw.slice(0, dot) : raw)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 70) || fallback;
  return `${stem}${ext}`;
}

export function validatePressKitModel(model) {
  const errors = [];
  if (!String(model.authorName || "").trim()) errors.push("Falta el nombre del autor.");
  if (!isEmail(model.contactEmail)) errors.push("El email de prensa no es válido.");
  if (!String(model.bioShort || "").trim()) errors.push("Falta la biografía corta.");
  if (!String(model.bookTitle || "").trim()) errors.push("Falta el título del libro.");
  if (!String(model.bookDescription || "").trim()) errors.push("Falta la descripción/sinopsis del libro.");
  if (!['contact_only','editorial_use'].includes(model.assetPermission)) errors.push("Selecciona una política de uso de imágenes.");
  if (model.website && !isHttpsUrl(model.website)) errors.push("La web debe usar HTTPS.");
  return errors;
}

export function buildTextFiles(model, assetSummary = []) {
  const authorSlug = slugify(model.authorName);
  const bookSlug = slugify(model.bookTitle);
  const generated = new Date().toISOString().slice(0, 10);
  const topics = splitLines(model.interviewTopics);

  const authorData = cleanObject({
    name: model.authorName.trim(),
    pressContact: model.contactEmail.trim(),
    website: clean(model.website),
    shortBio: model.bioShort.trim(),
    longBio: clean(model.bioLong),
    social: clean(model.socialLinks),
  });

  const bookData = cleanObject({
    title: model.bookTitle.trim(),
    publisher: clean(model.publisher),
    isbn: clean(model.isbn),
    publicationDate: clean(model.publicationDate),
    price: clean(model.price),
    description: model.bookDescription.trim(),
    purchaseUrl: clean(model.purchaseUrl),
  });

  const permission = model.assetPermission === 'editorial_use'
    ? `El autor declara que dispone de los derechos necesarios sobre los archivos incluidos y autoriza su reproducción editorial para informar sobre el autor y/o el libro, con atribución cuando corresponda. Esta autorización procede de la selección realizada por el usuario al generar el paquete; conviene sustituir este texto si existen condiciones específicas.`
    : `Los archivos se incluyen para identificación y consulta. Para reproducir fotografías, portadas u otros assets, contactar previamente con: ${model.contactEmail.trim()}.`;

  const checklist = [];
  if (!model.bioLong?.trim()) checklist.push("Añadir una biografía larga si el medio la necesita.");
  if (!model.publisher?.trim()) checklist.push("Completar editorial/sello si aplica.");
  if (!model.isbn?.trim()) checklist.push("Completar ISBN si existe y es público.");
  if (!model.publicationDate?.trim()) checklist.push("Completar fecha de publicación si está confirmada.");
  if (!model.purchaseUrl?.trim()) checklist.push("Añadir enlace oficial de compra/información cuando exista.");
  if (!topics.length) checklist.push("Añadir temas o preguntas posibles de entrevista.");
  if (!assetSummary.some(x => x.role === 'author')) checklist.push("Añadir al menos una fotografía de autor en buena resolución.");
  if (!assetSummary.some(x => x.role === 'cover')) checklist.push("Añadir la portada del libro cuando se pueda distribuir a prensa.");

  const readme = [
    `KIT DE PRENSA — ${model.authorName.trim()}`,
    `Libro destacado: ${model.bookTitle.trim()}`,
    `Generado: ${generated}`,
    "",
    "CONTENIDO",
    "- datos/autor.json — datos estructurados del autor introducidos por el usuario.",
    "- datos/libro.json — ficha del libro introducida por el usuario.",
    "- textos/biografia-corta.txt — bio lista para copiar.",
    model.bioLong?.trim() ? "- textos/biografia-larga.txt — bio larga lista para copiar." : null,
    "- textos/sinopsis.txt — descripción/sinopsis suministrada por el usuario.",
    topics.length ? "- textos/temas-entrevista.txt — temas suministrados por el usuario." : null,
    "- PERMISOS_ASSETS.txt — política de uso seleccionada al generar el paquete.",
    "- MANIFEST.json — inventario y hashes SHA-256.",
    "- CHECKSUMS_SHA256.txt — comprobación de integridad.",
    assetSummary.length ? "- assets/ — archivos locales añadidos por el usuario." : null,
    "",
    "CONTACTO DE PRENSA",
    model.contactEmail.trim(),
    model.website?.trim() || null,
    "",
    "NOTA",
    "Este paquete se ha generado localmente en el navegador. El generador no comprueba que premios, citas, fechas, derechos o datos editoriales sean ciertos: la responsabilidad de esos datos corresponde a quien los introduce.",
  ].filter(Boolean).join("\n");

  const files = {
    "README.txt": readme,
    "datos/autor.json": JSON.stringify(authorData, null, 2) + "\n",
    "datos/libro.json": JSON.stringify(bookData, null, 2) + "\n",
    "textos/biografia-corta.txt": model.bioShort.trim() + "\n",
    "textos/sinopsis.txt": model.bookDescription.trim() + "\n",
    "PERMISOS_ASSETS.txt": permission + "\n",
  };
  if (model.bioLong?.trim()) files["textos/biografia-larga.txt"] = model.bioLong.trim() + "\n";
  if (topics.length) files["textos/temas-entrevista.txt"] = topics.map((t, i) => `${i + 1}. ${t}`).join("\n") + "\n";
  if (checklist.length) files["PENDIENTES_RECOMENDADOS.txt"] = checklist.map(x => `- ${x}`).join("\n") + "\n";

  return { files, authorSlug, bookSlug, checklist, authorData, bookData };
}

export async function sha256Hex(data) {
  const bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export function splitLines(value) {
  return String(value || "").split(/\r?\n/).map(x => x.trim()).filter(Boolean).slice(0, 20);
}

function clean(value) { const v = String(value || "").trim(); return v || undefined; }
function cleanObject(obj) { return Object.fromEntries(Object.entries(obj).filter(([,v]) => v !== undefined && v !== "")); }
function isEmail(v) { return /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/i.test(String(v || "").trim()); }
function isHttpsUrl(v) { try { return new URL(v).protocol === "https:"; } catch { return false; } }
