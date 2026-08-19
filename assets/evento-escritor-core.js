export function validateEventModel(model) {
  const errors = [];
  if (!clean(model.name)) errors.push('Falta el nombre del evento.');
  if (!isHttps(model.url)) errors.push('La URL del evento debe ser HTTPS y única para ese evento.');
  if (!clean(model.venueName)) errors.push('Falta el nombre del lugar.');
  if (!clean(model.streetAddress)) errors.push('Falta la dirección postal.');
  if (!clean(model.addressLocality)) errors.push('Falta la localidad.');
  if (!clean(model.addressCountry)) errors.push('Falta el país.');
  if (!model.confirmed) errors.push('Solo se generan eventos confirmados.');

  if (model.allDay) {
    if (!isDateOnly(model.startDate)) errors.push('Falta una fecha de inicio válida.');
    if (model.endDate && !isDateOnly(model.endDate)) errors.push('La fecha final no es válida.');
    if (model.endDate && model.endDate < model.startDate) errors.push('La fecha final no puede ser anterior al inicio.');
  } else {
    if (!isLocalDateTime(model.startDateTime)) errors.push('Falta fecha y hora de inicio.');
    if (!isOffset(model.utcOffset)) errors.push('El offset UTC debe tener formato +02:00, +01:00, etc.');
    if (model.endDateTime && !isLocalDateTime(model.endDateTime)) errors.push('La fecha/hora final no es válida.');
    if (isLocalDateTime(model.startDateTime) && isOffset(model.utcOffset)) {
      const start = parseOffsetDate(model.startDateTime, model.utcOffset);
      if (!Number.isFinite(start.getTime())) errors.push('No se pudo interpretar la fecha de inicio.');
      if (model.endDateTime) {
        const end = parseOffsetDate(model.endDateTime, model.utcOffset);
        if (!Number.isFinite(end.getTime()) || end <= start) errors.push('La hora final debe ser posterior al inicio.');
      }
    }
  }

  for (const [label, value] of [['imagen', model.imageUrl], ['organizador', model.organizerUrl]]) {
    if (value && !isHttps(value)) errors.push(`La URL de ${label} debe usar HTTPS.`);
  }
  return errors;
}

export function buildEventOutputs(model) {
  const errors = validateEventModel(model);
  if (errors.length) throw new Error(errors.join(' '));

  const jsonLd = buildJsonLd(model);
  const html = buildVisibleHtml(model);
  const ics = buildIcs(model);
  const filename = `evento-${slugify(model.name)}-${eventDateKey(model)}.ics`;
  return { jsonLd, html, ics, filename };
}

export function buildJsonLd(model) {
  const location = {
    '@type': 'Place',
    name: clean(model.venueName),
    address: compact({
      '@type': 'PostalAddress',
      streetAddress: clean(model.streetAddress),
      addressLocality: clean(model.addressLocality),
      postalCode: clean(model.postalCode),
      addressRegion: clean(model.addressRegion),
      addressCountry: clean(model.addressCountry),
    }),
  };

  const event = compact({
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: clean(model.name),
    description: clean(model.description),
    startDate: schemaStart(model),
    endDate: schemaEnd(model),
    eventStatus: 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
    location,
    url: clean(model.url),
    image: clean(model.imageUrl),
    organizer: clean(model.organizerName) ? compact({
      '@type': 'Person',
      name: clean(model.organizerName),
      url: clean(model.organizerUrl),
    }) : undefined,
  });
  return JSON.stringify(event, null, 2)
    .replace(/</g, '\\u003c')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

export function buildVisibleHtml(model) {
  const start = schemaStart(model);
  const end = schemaEnd(model);
  const dateText = model.allDay
    ? formatDateEs(model.startDate, model.endDate)
    : formatDateTimeEs(model.startDateTime, model.endDateTime, model.utcOffset);

  const address = [model.venueName, model.streetAddress, model.postalCode, model.addressLocality, model.addressRegion, model.addressCountry]
    .map(clean).filter(Boolean).join(', ');

  return `<article class="event-card">
  <h2>${escapeHtml(model.name)}</h2>
  <p><time datetime="${escapeAttr(start)}">${escapeHtml(dateText)}</time></p>
  <p>${escapeHtml(address)}</p>${model.description ? `
  <p>${escapeHtml(model.description)}</p>` : ''}
  <p><a href="${escapeAttr(model.url)}">Información del evento</a></p>
</article>`;
}

export function buildIcs(model) {
  const uidSource = `${model.url}|${schemaStart(model)}|${model.name}`;
  const uid = `${fnv1a(uidSource)}@davidportodiaz.com`;
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//davidportodiaz.com//Generador de eventos para escritores//ES',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${toIcsUtc(new Date())}`,
  ];

  if (model.allDay) {
    lines.push(`DTSTART;VALUE=DATE:${dateOnlyToIcs(model.startDate)}`);
    const exclusiveEnd = addDays(model.endDate || model.startDate, 1);
    lines.push(`DTEND;VALUE=DATE:${dateOnlyToIcs(exclusiveEnd)}`);
  } else {
    lines.push(`DTSTART:${toIcsUtc(parseOffsetDate(model.startDateTime, model.utcOffset))}`);
    if (model.endDateTime) lines.push(`DTEND:${toIcsUtc(parseOffsetDate(model.endDateTime, model.utcOffset))}`);
  }

  lines.push(`SUMMARY:${escapeIcs(model.name)}`);
  if (model.description) lines.push(`DESCRIPTION:${escapeIcs(model.description)}`);
  lines.push(`LOCATION:${escapeIcs([model.venueName, model.streetAddress, model.postalCode, model.addressLocality, model.addressRegion, model.addressCountry].map(clean).filter(Boolean).join(', '))}`);
  lines.push(`URL:${escapeIcs(model.url)}`);
  lines.push('STATUS:CONFIRMED', 'END:VEVENT', 'END:VCALENDAR');

  return lines.map(foldIcsLine).join('\r\n') + '\r\n';
}

export function foldIcsLine(line) {
  const encoder = new TextEncoder();
  const chunks = [];
  let current = '';
  let limit = 75;
  for (const char of Array.from(String(line))) {
    const candidate = current + char;
    if (encoder.encode(candidate).length > limit && current) {
      chunks.push(current);
      current = char;
      limit = 74; // continuation line starts with one SPACE byte
    } else {
      current = candidate;
    }
  }
  if (current || !chunks.length) chunks.push(current);
  return chunks.join('\r\n ');
}

export function escapeIcs(value) {
  return String(value || '').replace(/\\/g, '\\\\').replace(/\r?\n/g, '\\n').replace(/,/g, '\\,').replace(/;/g, '\\;');
}

export function parseOffsetDate(local, offset) {
  return new Date(`${local}:00${offset}`);
}

function schemaStart(model) {
  return model.allDay ? model.startDate : `${model.startDateTime}:00${model.utcOffset}`;
}
function schemaEnd(model) {
  if (model.allDay) return model.endDate || undefined;
  return model.endDateTime ? `${model.endDateTime}:00${model.utcOffset}` : undefined;
}
function eventDateKey(model) { return (model.allDay ? model.startDate : model.startDateTime.slice(0,10)).replace(/-/g,''); }
function dateOnlyToIcs(value) { return String(value).replace(/-/g,''); }
function toIcsUtc(date) { return date.toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'); }
function addDays(dateOnly, days) { const d = new Date(`${dateOnly}T00:00:00Z`); d.setUTCDate(d.getUTCDate()+days); return d.toISOString().slice(0,10); }
function isDateOnly(v) { return /^\d{4}-\d{2}-\d{2}$/.test(String(v||'')) && Number.isFinite(new Date(`${v}T00:00:00Z`).getTime()); }
function isLocalDateTime(v) { return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(String(v||'')); }
function isOffset(v) {
  const m = String(v || '').match(/^([+-])(\d{2}):([0-5]\d)$/);
  if (!m) return false;
  const hours = Number(m[2]);
  const minutes = Number(m[3]);
  return hours < 14 || (hours === 14 && minutes === 0);
}
function isHttps(v) { try { const u = new URL(String(v||'')); return u.protocol === 'https:' && !u.username && !u.password; } catch { return false; } }
function clean(v) { const s=String(v||'').trim(); return s || undefined; }
function compact(obj) { return Object.fromEntries(Object.entries(obj).filter(([,v]) => v !== undefined && v !== '')); }
function slugify(v) { return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,70) || 'evento'; }
function fnv1a(value) { let h=0x811c9dc5; for(const c of new TextEncoder().encode(value)){ h ^= c; h = Math.imul(h,0x01000193) >>> 0; } return h.toString(16).padStart(8,'0'); }
function escapeHtml(v) { return String(v||'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function escapeAttr(v) { return escapeHtml(v); }
function formatDateEs(start,end) { return end && end!==start ? `${start} — ${end}` : start; }
function formatDateTimeEs(start,end,offset) { return end ? `${start.replace('T',' ')} — ${end.replace('T',' ')} (UTC${offset})` : `${start.replace('T',' ')} (UTC${offset})`; }
