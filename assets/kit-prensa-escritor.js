import { slugify, sanitizeFilename, validatePressKitModel, buildTextFiles, sha256Hex, formatMiB } from './kit-prensa-core.js';
import { strToU8, zipStoreSync, ZIP_EPOCH } from './zip-store-lite.js';

const root = document.querySelector('[data-press-kit-builder]');
if (root) init(root);

function init(root) {
  const form = root.querySelector('form');
  const status = root.querySelector('[data-kit-status]');
  const submit = root.querySelector('[data-kit-submit]');
  const summary = root.querySelector('[data-kit-summary]');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const model = modelFromForm(form);
    const errors = validatePressKitModel(model);
    if (errors.length) {
      setStatus(errors.join(' '), true);
      return;
    }

    let assets;
    try {
      assets = collectAssetFiles(form);
    } catch (error) {
      setStatus(error.message || 'No se pudieron leer los archivos.', true);
      return;
    }
    const totalBytes = assets.reduce((sum, item) => sum + item.file.size, 0);
    if (totalBytes > 25 * 1024 * 1024) {
      setStatus('Los assets superan 25 MiB. Reduce el tamaño antes de generar el kit.', true);
      return;
    }

    setBusy(true);
    setStatus('Preparando archivos y calculando integridad…', false);

    try {
      const assetSummary = assets.map(a => ({ role: a.role, originalName: a.file.name, size: a.file.size, type: a.file.type }));
      const built = buildTextFiles(model, assetSummary);
      const archive = {};
      const manifestFiles = [];

      for (const path of Object.keys(built.files).sort()) {
        const bytes = strToU8(built.files[path]);
        archive[path] = bytes;
        manifestFiles.push(await manifestEntry(path, bytes, 'generated'));
      }

      const usedNames = new Set();
      for (const asset of assets.sort((a, b) => a.file.name.localeCompare(b.file.name, 'es'))) {
        const bytes = new Uint8Array(await asset.file.arrayBuffer());
        const safe = uniqueName(`${asset.role}-${safeAssetFilename(asset.file, asset.role)}`, usedNames);
        const path = `assets/${safe}`;
        archive[path] = bytes;
        manifestFiles.push(await manifestEntry(path, bytes, asset.role, asset.file.type));
      }

      const manifest = {
        schema: 'davidportodiaz.com/press-kit-builder/v1',
        generatedBy: 'Generador de kit de prensa para escritores',
        author: model.authorName.trim(),
        book: model.bookTitle.trim(),
        files: manifestFiles.sort((a, b) => a.path.localeCompare(b.path)),
        privacy: 'Generado localmente en el navegador; los archivos seleccionados no se suben al generador.',
      };

      const manifestBytes = strToU8(JSON.stringify(manifest, null, 2) + '\n');
      archive['MANIFEST.json'] = manifestBytes;

      const checksumEntries = [...manifestFiles, await manifestEntry('MANIFEST.json', manifestBytes, 'generated')]
        .sort((a, b) => a.path.localeCompare(b.path));
      const checksums = checksumEntries.map(x => `${x.sha256}  ${x.path}`).join('\n') + '\n';
      archive['CHECKSUMS_SHA256.txt'] = strToU8(checksums);

      const zip = zipStoreSync(archive, { mtime: ZIP_EPOCH });
      const blob = new Blob([zip], { type: 'application/zip' });
      const filename = `kit-prensa-${slugify(model.authorName)}-${slugify(model.bookTitle)}.zip`;
      download(blob, filename);

      renderSummary(summary, built, assets, blob.size, filename);
      setStatus('Kit generado. Revisa el ZIP antes de enviarlo a un medio.', false);
    } catch (error) {
      console.error(error);
      setStatus('No se pudo generar el ZIP. Revisa los archivos e inténtalo de nuevo.', true);
    } finally {
      setBusy(false);
    }
  });

  function setBusy(busy) {
    submit.disabled = busy;
    submit.textContent = busy ? 'Generando…' : 'Generar ZIP';
  }
  function setStatus(message, error) {
    status.textContent = message;
    status.dataset.state = error ? 'error' : 'normal';
    status.setAttribute('role', error ? 'alert' : 'status');
  }

  const processor = root.querySelector('[data-publishing-processor]');
  if (processor) {
    processor.inert = false;
    processor.removeAttribute('inert');
    processor.removeAttribute('aria-disabled');
  }
}

function modelFromForm(form) {
  const data = new FormData(form);
  return {
    authorName: data.get('authorName'),
    contactEmail: data.get('contactEmail'),
    website: data.get('website'),
    socialLinks: data.get('socialLinks'),
    bioShort: data.get('bioShort'),
    bioLong: data.get('bioLong'),
    bookTitle: data.get('bookTitle'),
    publisher: data.get('publisher'),
    isbn: data.get('isbn'),
    publicationDate: data.get('publicationDate'),
    price: data.get('price'),
    purchaseUrl: data.get('purchaseUrl'),
    bookDescription: data.get('bookDescription'),
    interviewTopics: data.get('interviewTopics'),
    assetPermission: data.get('assetPermission'),
  };
}

const MAX_ASSETS = 10;
const MIME_EXT = new Map([['image/jpeg','.jpg'],['image/png','.png'],['image/webp','.webp'],['application/pdf','.pdf']]);
const ACCEPTED_MIME = new Set(MIME_EXT.keys());

function collectAssetFiles(form) {
  const result = [];
  const rejected = [];
  for (const [field, role] of [['authorPhotos', 'author'], ['coverFiles', 'cover'], ['otherFiles', 'other']]) {
    const input = form.elements[field];
    for (const file of input?.files || []) {
      if (!ACCEPTED_MIME.has(file.type)) {
        rejected.push(file.name);
        continue;
      }
      if (file.size > 12 * 1024 * 1024) throw new Error(`Archivo demasiado grande: ${file.name}`);
      result.push({ role, file });
    }
  }
  if (rejected.length) {
    throw new Error(`Formato no admitido: ${rejected.join(', ')}. Se aceptan JPG, PNG, WebP y PDF.`);
  }
  if (result.length > MAX_ASSETS) {
    throw new Error(`Has seleccionado ${result.length} archivos y el máximo es ${MAX_ASSETS}. Quita ${result.length - MAX_ASSETS} y vuelve a generar el kit.`);
  }
  return result;
}

function safeAssetFilename(file, fallback) {
  const normalized = sanitizeFilename(file.name, fallback);
  const dot = normalized.lastIndexOf('.');
  const stem = dot > 0 ? normalized.slice(0, dot) : normalized;
  return `${stem}${MIME_EXT.get(file.type)}`;
}

async function manifestEntry(path, bytes, role, mime = 'text/plain') {
  return { path, role, mime, size: bytes.byteLength, sha256: await sha256Hex(bytes) };
}

function uniqueName(name, used) {
  let candidate = name;
  let n = 2;
  const dot = name.lastIndexOf('.');
  const stem = dot > 0 ? name.slice(0, dot) : name;
  const ext = dot > 0 ? name.slice(dot) : '';
  while (used.has(candidate)) candidate = `${stem}-${n++}${ext}`;
  used.add(candidate);
  return candidate;
}

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function renderSummary(el, built, assets, size, filename) {
  const mib = formatMiB(size);
  el.hidden = false;
  el.replaceChildren();
  const strong = document.createElement('strong');
  strong.textContent = filename;
  const span = document.createElement('span');
  span.textContent = `${mib} MiB · ${assets.length} asset(s) · ${built.checklist.length} pendiente(s) recomendado(s)`;
  el.append(strong, span);
}
