import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';

// Taxonomía de descubrimiento (#1009): /editoriales/ ofrecía 104 etiquetas exactas y el radar 50.
// «fantasía» exacta devolvía 54 editoriales y dejaba fuera a Siruela (fantástico), Andrómeda
// (romantasy, fantasía oscura), Cetus, Vanadis o Dilatando Mentes (fantasía oscura). Las familias
// de data/genre-families.json las reúnen, cada ficha explica qué etiqueta literal la hace aparecer
// y la etiqueta exacta sigue disponible con el mismo resultado de antes.
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const taxonomy = JSON.parse(readFileSync(new URL('../data/genre-families.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ headless: true });

async function open(path, { width = 1280, javaScriptEnabled = true } = {}) {
  const context = await browser.newContext({ viewport: { width, height: 844 }, javaScriptEnabled, reducedMotion: 'reduce' });
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(origin + path, { waitUntil: 'load' });
  return { context, page, errors };
}
const cards = page => page.locator('[data-editorial-card]').evaluateAll(list => list.map(c => ({
  name: c.dataset.name, hidden: c.hidden, families: (c.dataset.families || '').split('|').filter(Boolean),
  tags: [...c.querySelectorAll('.editorial-genre')].map(t => t.textContent.trim()),
  matched: [...c.querySelectorAll('.editorial-genre.is-match')].map(t => t.textContent.trim()),
  note: c.querySelector('[data-genre-match]')?.hidden === false ? c.querySelector('[data-genre-match]').textContent.trim() : '',
  status: c.dataset.status,
})));
const fantasyTags = new Set(taxonomy.families.find(f => f.id === 'fantasia').tags);

try {
  // 1. Pocas familias primero; las etiquetas literales siguen disponibles aparte.
  {
    const { context, page, errors } = await open('/editoriales/');
    const groups = await page.locator('[data-editoriales-genre] optgroup').evaluateAll(gs => gs.map(g => ({ label: g.label, n: g.querySelectorAll('option').length })));
    assert.equal(groups.length, 2, 'el selector separa familias y etiquetas exactas');
    assert.match(groups[0].label, /Familias/);
    assert.ok(groups[0].n >= 8 && groups[0].n <= 14, `familias iniciales: ${groups[0].n}`);
    assert.match(groups[1].label, /Etiqueta exacta/);
    assert.equal(groups[1].n, 104, 'no se pierde ninguna etiqueta literal de la fuente');
    const total = (await cards(page)).length;

    // 2. «Tengo una novela de fantasía»: la familia descubre variantes y explica por qué.
    await page.selectOption('[data-editoriales-genre]', 'familia:fantasia');
    const all = await cards(page);
    const shown = all.filter(c => !c.hidden);
    for (const name of ['Ediciones Siruela', 'Editorial Andrómeda', 'Cetus Editorial', 'Editorial Vanadis', 'Dilatando Mentes Editorial']) {
      assert.ok(shown.some(c => c.name === name), `familia Fantasía no descubre ${name}`);
    }
    assert.ok(shown.length > 54, `familia Fantasía debe ampliar las 54 de la etiqueta exacta (${shown.length})`);
    for (const c of shown) {
      assert.ok(c.tags.some(t => fantasyTags.has(t)), `${c.name} aparece sin ninguna etiqueta de la familia: ${c.tags}`);
      assert.ok(c.matched.length > 0 && c.matched.every(t => fantasyTags.has(t)), `${c.name}: resalta ${c.matched}`);
      assert.match(c.note, /Aparece en «Fantasía y fantástico» porque declara: .+\. Comprueba estado y condiciones antes de enviar\./, `${c.name}: nota «${c.note}»`);
      for (const t of c.matched) assert.ok(c.note.includes(t), `${c.name}: la nota no nombra ${t}`);
      assert.doesNotMatch(c.note, /acepta|abierta/i, 'la familia no promete aceptación ni apertura');
    }
    // Negativos: lo que no declara ninguna variante no entra (poesía, ensayo, thriller solos...).
    for (const c of all.filter(c => c.hidden)) assert.ok(!c.tags.some(t => fantasyTags.has(t)), `${c.name} declara ${c.tags} y queda fuera`);
    assert.ok(all.some(c => c.hidden && c.tags.includes('poesía')), 'hay fichas de poesía que la familia no debe incluir');
    // El estado sigue visible antes de decidir: cada ficha conserva su insignia.
    assert.equal(await page.locator('[data-editorial-card]:not([hidden]) .editorial-card__head .editorial-badge, [data-editorial-card]:not([hidden]) .editorial-card__head [class*="status"]').count() >= shown.length, true);
    assert.match(page.url(), /#genero=familia%3Afantasia$/, 'la familia queda en la URL compartible');
    // La nota generada no forma parte del texto buscable: sin esto, buscar su propia frase
    // devolvía todas las fichas de la familia.
    await page.fill('[data-editoriales-search]', 'comprueba estado y condiciones');
    assert.equal((await cards(page)).filter(c => !c.hidden).length, 0, 'la búsqueda encuentra el texto de la nota de familia');
    await page.fill('[data-editoriales-search]', '');

    // 3. Combinación: familia + estado es conjunción; Limpiar restablece todo.
    await page.selectOption('[data-editoriales-status]', 'open');
    const combo = (await cards(page)).filter(c => !c.hidden);
    assert.ok(combo.length > 0 && combo.length < shown.length);
    assert.ok(combo.every(c => c.status === 'open' && c.families.includes('fantasia')));
    await page.locator('[data-editoriales-reset]').click();
    const cleared = await cards(page);
    assert.equal(cleared.filter(c => !c.hidden).length, total);
    assert.ok(cleared.every(c => !c.note && !c.matched.length), 'Limpiar deja notas o resaltados');
    assert.doesNotMatch(page.url(), /genero=/);

    // 4. La etiqueta exacta conserva el resultado de antes y no añade notas de familia.
    await page.selectOption('[data-editoriales-genre]', 'fantasía');
    const exact = (await cards(page)).filter(c => !c.hidden);
    assert.equal(exact.length, 54);
    assert.ok(exact.every(c => c.tags.includes('fantasía') && c.matched.join() === 'fantasía' && !c.note));

    // 5. Romantasy pertenece a dos familias; romántica no arrastra fantasía pura.
    await page.selectOption('[data-editoriales-genre]', 'familia:romantica');
    const romance = (await cards(page)).filter(c => !c.hidden);
    assert.ok(romance.some(c => c.name === 'Editorial Andrómeda'));
    assert.ok(romance.every(c => !c.tags.every(t => ['fantasía', 'ciencia ficción', 'terror'].includes(t))));
    assert.deepEqual(errors, []);
    await context.close();
  }

  // 6. URL compartida y búsqueda libre por el nombre de la familia.
  {
    const { context, page } = await open('/editoriales/#genero=familia:fantasia&estado=open');
    assert.equal(await page.locator('[data-editoriales-genre]').inputValue(), 'familia:fantasia');
    const restored = (await cards(page)).filter(c => !c.hidden);
    assert.ok(restored.length > 0 && restored.every(c => c.status === 'open' && c.families.includes('fantasia')));
    await page.goto(origin + '/editoriales/#genero=familia:inventada', { waitUntil: 'load' });
    assert.equal(await page.locator('[data-editoriales-genre]').inputValue(), '', 'una familia desconocida en la URL no filtra');
    await page.fill('[data-editoriales-search]', 'fantasía');
    const siruela = (await cards(page)).find(c => c.name === 'Ediciones Siruela');
    assert.equal(siruela.hidden, false, 'buscar «fantasía» no encuentra a Siruela («fantástico»)');
    assert.match(siruela.note, /familia «Fantasía y fantástico»: declara fantástico/);
    await context.close();
  }

  // 7. Teclado y reflow a 390 px.
  {
    const { context, page } = await open('/editoriales/', { width: 390 });
    await page.locator('[data-editoriales-genre]').focus();
    await page.keyboard.press('ArrowDown');
    assert.match(await page.locator('[data-editoriales-genre]').inputValue(), /^familia:/, 'el teclado llega primero a las familias');
    await page.selectOption('[data-editoriales-genre]', 'familia:terror');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 0, `390px: scroll horizontal de ${overflow} px`);
    const top = await page.locator('[data-editorial-card]:not([hidden])').first().evaluate(e => Math.round(e.getBoundingClientRect().top + scrollY));
    console.log(`390px editoriales: primera ficha a ${top} px`);
    await context.close();
  }

  // 8. Radar: la familia Relato reúne relato corto, microrrelato... y explica la coincidencia.
  {
    const { context, page, errors } = await open('/convocatorias-escritores/');
    const groups = await page.locator('[data-radar-genre] optgroup').evaluateAll(gs => gs.map(g => g.querySelectorAll('option').length));
    assert.equal(groups.length, 2);
    assert.ok(groups[0] <= 14);
    const relato = new Set(taxonomy.families.find(f => f.id === 'relato').tags);
    await page.selectOption('[data-radar-genre]', 'familia:relato');
    const items = await page.locator('[data-radar-item]').evaluateAll(list => list.map(i => ({ hidden: i.hidden, kind: i.dataset.radarKind || 'active', unavailable: i.dataset.radarUnavailable, genres: i.dataset.genres.split('|'), note: i.querySelector('[data-genre-match]')?.hidden === false ? i.querySelector('[data-genre-match]').textContent : '' })));
    const visible = items.filter(i => !i.hidden);
    assert.ok(visible.length > 0);
    assert.ok(visible.some(i => !i.genres.includes('relato')), 'la familia no amplía la etiqueta «relato»');
    for (const i of visible) {
      assert.ok(i.genres.some(g => relato.has(g)), `radar: ${i.genres} no pertenece a Relato`);
      assert.match(i.note, /^Aparece en «Cuento, relato y microrrelato» porque las bases declaran: .+\. Comprueba los requisitos/);
    }
    for (const i of items.filter(i => i.hidden && i.kind !== 'expired' && i.unavailable !== 'true')) assert.ok(!i.genres.some(g => relato.has(g)), `radar: ${i.genres} queda fuera`);
    // Exacta: sin notas y solo esa etiqueta.
    const exactValue = await page.locator('[data-radar-genre] optgroup:nth-of-type(2) option', { hasText: /^Microrrelato$/ }).getAttribute('value');
    await page.selectOption('[data-radar-genre]', exactValue);
    const exact = (await page.locator('[data-radar-item]:not([hidden])').evaluateAll(list => list.map(i => ({ genres: i.dataset.genres.split('|'), note: !i.querySelector('[data-genre-match]').hidden }))));
    assert.ok(exact.length > 0 && exact.every(i => i.genres.includes('microrrelato') && !i.note));
    await page.locator('[data-radar-clear]').click();
    assert.equal(await page.locator('[data-genre-match]:not([hidden])').count(), 0);
    assert.deepEqual(errors, []);
    await context.close();
  }

  // 9. Sin JS: fichas completas, sin notas vacías ni el mapa de familias a la vista.
  for (const path of ['/editoriales/', '/convocatorias-escritores/']) {
    const { context, page } = await open(path, { width: 390, javaScriptEnabled: false });
    assert.equal(await page.locator('[data-genre-match]:visible').count(), 0, `${path}: notas visibles sin JS`);
    assert.equal(await page.locator('[data-genre-families]').isVisible(), false);
    assert.doesNotMatch(await page.locator('main').innerText(), /"labels":/);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS writer resources genre families: families first, exact tags kept, explained matches, URL, radar, no-JS');
