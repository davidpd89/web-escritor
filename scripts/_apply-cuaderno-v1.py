#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

ARTICLES = [
    "cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/index.html",
    "cuaderno/que-es-el-portal-fantasy/index.html",
    "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
    "cuaderno/sistema-de-magia-noveris/index.html",
    "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
    "cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html",
    "cuaderno/worldbuilding-noveris-ciudad-magica/index.html",
]
FERIA = ROOT / ARTICLES[0]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, got {count}")
    return text.replace(old, new, 1)


def remove_once(text: str, old: str, label: str) -> str:
    return replace_once(text, old, "", label)


# 1) Editorial connections: max 3, while preserving the three destinations
# most directly related to the article. The Cuaderno breadcrumb already gives a
# semantic route back to /cuaderno/, so the repeated generic link is redundant.
for rel in ARTICLES:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    text = remove_once(text, '<a href="/cuaderno/">Volver al Cuaderno</a>', f"{rel}: generic Cuaderno related link")
    path.write_text(text, encoding="utf-8")

# FLM had five connections. Keep chapter, book and event continuity; the press
# kit remains reachable from the global information navigation and is less
# semantically direct than the event route for this chronicle.
text = FERIA.read_text(encoding="utf-8")
text = remove_once(text, '<a href="/prensa.html">Kit de prensa</a>', "FLM: press related link")

# Short chronicle: only two substantive H2 sections. The editorial contract says
# TOC is conditional (normally >=4 substantive H2 or a genuine navigation need),
# so this two-item TOC is interface noise rather than useful wayfinding.
pattern = re.compile(r'\n\s*<nav class="article-toc" aria-label="En esta página" data-article-toc>.*?</nav>\n', re.S)
text, count = pattern.subn("\n", text, count=1)
if count != 1:
    raise RuntimeError(f"FLM: expected one short TOC, got {count}")
FERIA.write_text(text, encoding="utf-8")

# 2) Editorial CSS: recompose article pages at tablet portrait / compact
# landscape widths instead of squeezing TOC + prose into two narrow columns.
css_path = ROOT / "assets/v1-editorial.css"
css = css_path.read_text(encoding="utf-8")
css = replace_once(
    css,
    'html.v1 .article-share-status{min-width:1px;font-size:var(--text-xs);color:var(--color-muted)}',
    'html.v1 .article-share-status{min-width:1px;font-size:var(--text-xs);color:var(--color-muted)}\n'
    'html.v1 .article-print-source{display:none}',
    "editorial CSS: print source screen state",
)
css = replace_once(
    css,
    'html.v1 .article-prose a{text-decoration-color:var(--color-accent)}',
    'html.v1 .article-prose a{text-decoration-color:var(--color-accent);overflow-wrap:anywhere}',
    "editorial CSS: long article links",
)
marker = '@media (max-width:767px){'
tablet = '''@media (min-width:768px) and (max-width:859px){
  html.v1 .article-header{grid-template-columns:1fr}
  html.v1 .article-meta{border-left:0;border-top:1px solid var(--color-border);padding:1rem 0 0;display:flex;flex-wrap:wrap;gap:.25rem 1rem}
  html.v1 .article-layout{display:block;padding-top:2.75rem}
  html.v1 .article-toc{position:static;max-height:none;margin:0 0 2.75rem;padding:1rem 0;border-bottom:1px solid var(--color-border);overflow-x:auto}
  html.v1 .article-toc ol{display:flex;gap:1rem;min-width:max-content}
  html.v1 .article-toc a{display:block;max-width:20ch}
  html.v1 .article-prose{max-width:var(--reading-max);margin-inline:auto}
  html.v1 .article-faq,html.v1 .article-end{display:block}
  html.v1 .article-faq__head,html.v1 .article-end__label{margin-bottom:1.5rem}
  html.v1 .article-faq__list,html.v1 .article-end__body{border-top:1px solid var(--color-border)}
}
'''
css = replace_once(css, marker, tablet + marker, "editorial CSS: tablet recomposition")
css = replace_once(
    css,
    '  html.v1 .article-faq__list{border-top:1px solid currentColor}\n}',
    '  html.v1 .article-faq__list{border-top:1px solid currentColor}\n'
    '  html.v1 .article-print-source{display:block;margin:2rem 0 0;padding-top:.8rem;border-top:1px solid currentColor;font:9pt/1.45 var(--font-ui);overflow-wrap:anywhere}\n}',
    "editorial CSS: print provenance",
)
css_path.write_text(css, encoding="utf-8")

# 3) Print utility: preserve canonical provenance in print/PDF generated from
# the V1 article button. Progressive enhancement; body stays complete without JS.
js_path = ROOT / "assets/v1-editorial.js"
js = js_path.read_text(encoding="utf-8")
old = '''  document.querySelectorAll('[data-print]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => window.print());
  });'''
new = '''  const ensurePrintSource = () => {
    const article = document.querySelector('.article-page article');
    if (!article || article.querySelector('.article-print-source')) return;
    const canonical = document.querySelector('link[rel="canonical"]')?.href || location.href;
    const title = article.querySelector('h1')?.textContent?.trim() || document.title;
    const source = document.createElement('p');
    source.className = 'article-print-source';
    source.setAttribute('aria-hidden', 'true');
    source.textContent = `${title} — ${canonical}`;
    article.appendChild(source);
  };

  document.querySelectorAll('[data-print]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      ensurePrintSource();
      window.print();
    });
  });'''
js = replace_once(js, old, new, "editorial JS: print provenance")
js_path.write_text(js, encoding="utf-8")

# 4) Strengthen intrinsic QA. No historical/base dependency is introduced.
qa_path = ROOT / "qa/cuaderno-browser.mjs"
qa = qa_path.read_text(encoding="utf-8")
qa = replace_once(
    qa,
    "    assert.equal(data.articleId, SITE + spec.route + '#article', `${spec.key}: @id Article`);\n  }",
    "    assert.equal(data.articleId, SITE + spec.route + '#article', `${spec.key}: @id Article`);\n"
    "    const articleSchema = flattenNodes(parsed).find(node => node['@type'] === 'Article');\n"
    "    assert.ok(norm(articleSchema?.headline), `${spec.key}: Article headline`);\n"
    "    assert.ok(norm(articleSchema?.description), `${spec.key}: Article description`);\n"
    "    assert.equal(articleSchema?.url, SITE + spec.route, `${spec.key}: Article url`);\n"
    "    assert.equal(articleSchema?.inLanguage, 'es', `${spec.key}: Article inLanguage`);\n"
    "    assert.ok(articleSchema?.author?.['@id'], `${spec.key}: Article author`);\n"
    "    assert.ok(articleSchema?.publisher?.['@id'], `${spec.key}: Article publisher`);\n"
    "    assert.ok(articleSchema?.isPartOf?.['@id'], `${spec.key}: Article isPartOf`);\n"
    "    assert.ok(articleSchema?.about, `${spec.key}: Article about`);\n"
    "    assert.ok(articleSchema?.mentions, `${spec.key}: Article mentions`);\n"
    "  }",
    "QA: Article schema properties",
)
qa = replace_once(
    qa,
    "  const toc = page.locator('[data-article-toc]');\n  if (await toc.count()) {\n    const missing = await toc.locator('a[href^=\"#\"]').evaluateAll(links => links.map(link => link.getAttribute('href')).filter(href => !document.querySelector(href)));\n    assert.deepEqual(missing, [], `${spec.key}: TOC apunta a destino inexistente`);\n  }",
    "  const toc = page.locator('[data-article-toc]');\n  if (await toc.count()) {\n"
    "    const tocCount = await toc.locator('a[href^=\"#\"]').count();\n"
    "    assert.ok(tocCount >= 4, `${spec.key}: TOC sin suficiente valor de navegación (${tocCount})`);\n"
    "    const missing = await toc.locator('a[href^=\"#\"]').evaluateAll(links => links.map(link => link.getAttribute('href')).filter(href => !document.querySelector(href)));\n"
    "    assert.deepEqual(missing, [], `${spec.key}: TOC apunta a destino inexistente`);\n"
    "  }\n\n"
    "  if (spec.kind === 'article') {\n"
    "    const relatedCount = await page.locator('.article-related a').count();\n"
    "    assert.ok(relatedCount >= 1 && relatedCount <= 3, `${spec.key}: conexiones editoriales ${relatedCount}, esperado 1–3`);\n"
    "  }",
    "QA: TOC value and related count",
)
qa = replace_once(
    qa,
    "  const imageProblems = await page.locator('main img').evaluateAll(images => images.map(img => ({\n    src: img.getAttribute('src'),\n    alt: img.getAttribute('alt'),\n    width: img.getAttribute('width'),\n    height: img.getAttribute('height'),\n    loading: img.getAttribute('loading'),\n    top: img.getBoundingClientRect().top + window.scrollY,\n  })).filter(item => item.alt === null || !item.width || !item.height));\n  assert.deepEqual(imageProblems, [], `${spec.key}: imágenes sin alt/dimensiones`);",
    "  const imageProblems = await page.locator('main img').evaluateAll(images => images.map(img => ({\n"
    "    src: img.getAttribute('src'),\n"
    "    alt: img.getAttribute('alt'),\n"
    "    width: img.getAttribute('width'),\n"
    "    height: img.getAttribute('height'),\n"
    "  })).filter(item => item.alt === null || !item.width || !item.height));\n"
    "  assert.deepEqual(imageProblems, [], `${spec.key}: imágenes sin alt/dimensiones`);\n"
    "  if (spec.key === 'feria') {\n"
    "    const galleryLoading = await page.locator('.article-gallery img').evaluateAll(images => images.map(img => img.getAttribute('loading')));\n"
    "    assert.ok(galleryLoading.length >= 1 && galleryLoading.every(value => value === 'lazy'), 'feria: media below-fold debe cargar lazy');\n"
    "    const hero = page.locator('.article-hero-figure img');\n"
    "    assert.equal(await hero.getAttribute('loading'), 'eager', 'feria: foto documental principal debe estar disponible sin lazy delay');\n"
    "  }",
    "QA: FLM media loading",
)
qa = qa.replace("for (const spec of [pages[0], pages.find(p => p.key === 'portal')]) {", "for (const spec of pages) {")
if qa.count("for (const spec of pages) {") < 6:
    raise RuntimeError("QA: expected zoom/text-spacing/reduced-motion loops to expand")
qa = replace_once(
    qa,
    "  assert.equal(new URL(page.url()).hash, '#contenido', 'teclado: skip link no salta a contenido');\n  assert.equal(await page.locator('[data-share-url]:visible').count(), 1, 'teclado: compartir no disponible con JS');",
    "  assert.equal(new URL(page.url()).hash, '#contenido', 'teclado: skip link no salta a contenido');\n"
    "  const firstToc = page.locator('[data-article-toc] a[href^=\"#\"]').first();\n"
    "  await firstToc.focus();\n"
    "  const firstTarget = await firstToc.getAttribute('href');\n"
    "  await page.keyboard.press('Enter');\n"
    "  assert.equal(new URL(page.url()).hash, firstTarget, 'teclado: TOC no navega al destino');\n"
    "  await page.locator('[data-explore-open]').focus();\n"
    "  await page.keyboard.press('Enter');\n"
    "  assert.equal(await page.locator('[data-explore-dialog]').evaluate(dialog => dialog.open), true, 'teclado: Explore no abre');\n"
    "  await page.keyboard.press('Escape');\n"
    "  assert.equal(await page.locator('[data-explore-dialog]').evaluate(dialog => dialog.open), false, 'teclado: Explore no cierra con Escape');\n"
    "  assert.equal(await page.locator('[data-share-url]:visible').count(), 1, 'teclado: compartir no disponible con JS');",
    "QA: keyboard TOC and Explore",
)
qa = replace_once(
    qa,
    "  await page.click('[data-print]');\n  assert.equal(await page.evaluate(() => window.__printed), 1, 'print: botón no llama window.print');\n  await page.emulateMedia({ media: 'print' });",
    "  await page.click('[data-print]');\n"
    "  assert.equal(await page.evaluate(() => window.__printed), 1, 'print: botón no llama window.print');\n"
    "  const printSource = page.locator('.article-print-source');\n"
    "  assert.equal(await printSource.count(), 1, 'print: falta procedencia canónica');\n"
    "  assert.match(await printSource.innerText(), /https:\\/\\/davidportodiaz\\.com\\/cuaderno\\/que-es-el-portal-fantasy\\//, 'print: procedencia sin canonical');\n"
    "  await page.emulateMedia({ media: 'print' });",
    "QA: print provenance existence",
)
qa = replace_once(
    qa,
    "    articleEnd: getComputedStyle(document.querySelector('.article-end')).display,\n  }));",
    "    articleEnd: getComputedStyle(document.querySelector('.article-end')).display,\n"
    "    source: getComputedStyle(document.querySelector('.article-print-source')).display,\n"
    "  }));",
    "QA: print provenance computed style",
)
qa = replace_once(
    qa,
    "  assert.equal(visible.articleEnd, 'none', 'print: cierre de navegación debe ocultarse');",
    "  assert.equal(visible.articleEnd, 'none', 'print: cierre de navegación debe ocultarse');\n"
    "  assert.notEqual(visible.source, 'none', 'print: procedencia canónica debe imprimirse');",
    "QA: print provenance visibility",
)
qa_path.write_text(qa, encoding="utf-8")

# 5) Builders are part of the dedicated gate so their execution is explicitly
# evidenced on the final SHA, not merely inferred from another workflow.
workflow_path = ROOT / ".github/workflows/cuaderno-browser-qa.yml"
workflow = workflow_path.read_text(encoding="utf-8")
workflow = replace_once(
    workflow,
    "      - name: Run Cuaderno WCAG2AA\n",
    "      - name: Check generated editorial outputs\n"
    "        run: |\n"
    "          python scripts/build-feed.py --check\n"
    "          python scripts/build-sitemap.py --check\n"
    "          python scripts/build-article-tools.py --check\n"
    "          python scripts/build-topic-collections.py --data data/topic-collections.json --root . --check\n\n"
    "      - name: Run Cuaderno WCAG2AA\n",
    "workflow: builder checks",
)
workflow_path.write_text(workflow, encoding="utf-8")

print("CUADERNO MIGRATION APPLIED")
