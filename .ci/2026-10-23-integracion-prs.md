# Integración PRs 2026-10-23 (sesión parcial)
main: 8f175f05 (sin merges nuevos en esta sesión).
- #669 (b60bd94f): aditivo (6 ficheros, schema+checker+tests), 14/15 OK, falta reflow-sitewide. BEHIND main, sin protección de rama. Pendiente merge.
- #703 (d1007838): diff real vs main = 10 ficheros; /apoyar/ solo se publica con registro `support-project` public (support_page_authorized). 35 OK, falta reflow-sitewide. Pendiente: retarget base a main (gh pr edit 703 --base main) + merge squash; #698 aporta 1 doc.
- #724 (cadena 717→720→721→724): merge de main en la rama (sin conflictos), pruebas amazon-*/reader-review/taxonomía/parity OK en local. CI falló content-indexes (Pagefind obsoleto) → regenerado y subido 22fb1792. Base cambiada a main, marcado ready. Tras CI verde: merge; cerrar #717/#720/#721 como incluidos.
- #692: merge main subido (e0f13355); fallos antiguos eran artefactos obsoletos (export abierto, supply-chain, artifact contract). CI relanzado.
- #716: obsoleto/conflictivo; 5 ISBN realmente ausentes en main (9788418053870, 9791387512446, 9791387949891, 9791387962036, 9791387994600). Lanzado reading-catalogue-sync en main (run 39941273076) para regenerar; cuando cree PR nuevo, cerrar #716 con referencia.
Worktrees temporales: ../web-escritor-int-amazon, -int-ed, -int-rc (eliminar al acabar).
Sin tocar qa-gpt ni puertos 9224/9225/9230.

## Actualización (2ª tanda)
- #669: auto-merge squash activado; update-branch hecho (branch BEHIND exigido por ruleset). Un bucle en segundo plano actualiza #703 cuando #669 se fusione.
- #703: base ya en main (10 ficheros), auto-merge activado; necesita update-branch tras #669.
- #724: 4 fallos reales corregidos en 86e36922: (1) contrato buy-cta: ahora espera evento por origen (comprar-amazon-header/home/manecillas), exactamente uno; (2) content-parity: Author Follow (amazon.es/stores/author) excluido de la regla "compra usa amzn.to"; (3) script.js bump a 202610-launch-30 + hashes + Pagefind; (4) baselines visuales de Manecillas: ficha cambió legítimamente (sección Opiniones + Author Follow) → capturados con workflow visual-regression-qa capture_baseline (run 39945117634); falta descargar artefacto "visual-baselines", reemplazar qa/visual-baselines/ y commit.
- #737 (catálogo 5 ediciones nuevas, ISBN 9788467083316, 9788466380096, 9788466685344, 9788401040740, 9788408074496): runs action_required aprobados vía API; CI en curso.
- #692: solo falta reflow-sitewide.

## Actualización (3ª tanda, 2026-10-23)
- #692 FUSIONADO (squash, d432918d). Estaba en borrador; marcado ready y fusionado con 13/13 checks OK.
- #724: causa real de content-parity = byte 0x08 (\b) en la regex de qa/content-parity-manecillas.mjs; corregido. Baselines Manecillas (3 PNG) tomados del artefacto visual-baselines del run 39945117634 (head 86e36922) y validados; commit e16e2e26. hostname-allowlist falló por cancelación (10 min), no por contenido. #717 NO está incluido (6 commits: auditor ASIN con slug + tests); mergeado en la rama, merge ebaca1ed. #720 y #721 sí incluidos.
- #669, #703, #737: BEHIND main, CI pendiente (reflow-sitewide/csp/browser). #669 y #703 con auto-merge.
- Producción: davidportodiaz.com 200, script v=202609-launch-29 = main previo; #692 aún sin desplegar (smoke en cola). Último build Pages API "errored" 3a4fdfaf (antiguo, no verificado si afecta).
- Worktrees eliminados: int-ed, int-rc. Pendiente: int-amazon (hasta fusionar #724).

## Actualización (4ª tanda, cierre)
- #703 FUSIONADA: c8624491 (/apoyar/ sigue 404 en producción: no publicada).
- #724 FUSIONADA: d14c734e (squash). Pasos: merge de main dos veces (solo conflictos en Pagefind generado), regeneración de catálogo (11 ficheros) y Pagefind; un fallo CLS en /autor.html@768 fue flaky (pasó al reintento).
- #717/#720/#721 CERRADAS como superseded por #724: diff vs main revisado fichero a fichero; main contiene versiones iguales o posteriores (p. ej. ASIN_RE con slug de #717).
- Deploy Pages (workflow_dispatch) run 39982224490 sobre d14c734e: success. Producción sirve script.js?v=202610-launch-30.
- Smoke producción: 200 en /, /autor.html, /las-manecillas-del-recuerdo/, /libros/samuel-entre-mundos/, /recomendaciones/, sitemap, pagefind-entry; sin errores de consola; enlaces Amazon: compra + #customerReviews + Author Follow (stores/author) en autor y Samuel; Manecillas usa amzn.to + sección Opiniones sin enlace de reseña. /atlas/ y /apoyar/ = 404 (no publicados, esperado).
- Worktree ../web-escritor-int-amazon y rama int/amazon-chain eliminados.
- #669: actualizada a main d14c734e (auto-merge squash activo); CI rehecho, pendiente reflow-sitewide.
