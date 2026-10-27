# Revision humana asistida de los lotes qa-gpt (2026-10-26 / 27)

Constancia de la revision de las PRs de riesgo medio que el pipeline dejo para revision humana, y de las PRs de lote cerradas por CI roja. No sustituye al informe de la noche (`informe-qa-gpt-noche-2026-10-26`), que no esta en `main` ni en `automation/qa-gpt`.

## Fusionadas
- Las dos de revision: #886 (enlace nativo en `offline.html`) y #887 (enlace Eventos -> ficha de Aranjuez).
- Originales pequenas: #751 y #753 (lecturas: JSON-LD sin fixture y fechas en espanol), #896 (14 tests de proteccion).
- Recuperadas en PRs nuevas, con cada test fallando en `main` y pasando con el arreglo:
  - #904 QA de `tools-events-memory` (submit `.sr-only`).
  - #906 CSP con hashes en `offline.html` y `video-ios-test`.
  - #908 presupuesto de `catalogue-runtime` con valores reales.
  - #910 club (`aria-describedby`), eventos (gratuidad), radar (notas) y Pagefind.
  - #918 nueve borradores: lecturas (#756, #763), busqueda con `n` (#769), anuncio del newsletter (#782), `method="post"` sin JS (#785), registro de eventos (#786), avisos `noscript` (#789, #791) y aserciones Lighthouse (#806).
  - #919 validacion de URLs HTTPS en writer-tools (#764) y canonicos de colecciones (#803).

## Causas de los rojos de los lotes
- `browser-qa` "Guardar ficha" `tabindex=-1`: `qa/tools-events-memory-browser.mjs` no admitia los submit `.sr-only` que #868 saco del Tab a proposito. El workflow solo corre en PRs que tocan sus rutas, asi que #868 no lo ejecuto. El `curl: (7)` del log es el primer intento del bucle de espera, no el fallo.
- `performance-budget`: #903 declaraba 45189 B / 2 requests; lo real son 63497 B / 3 (el CSS carga una fuente).
- `radar HTML drifted from builder`: #884 cambiaba `data/radar-opportunities.json` sin regenerar `convocatorias-escritores/`.
- Hash CSP de #759 obsoleto tras #886; recalculado en #906. El QA `pwa-offline` inyecta su hoja de estres con `bypassCSP`.
- Paginas generadas editadas a mano (`editoriales/index.html`, #789): el cambio va en el builder. Los assets cambiados exigen subir `?v=` y registrar el hash (`check-asset-versions`).
- Rojos de reloj, no de las PRs: el radar publicado caduca con el cambio de dia en Madrid (`check-professional-resources`, `test-radar-freshness-real-clock`) hasta que el workflow `Refresh radar clock outputs` abre su PR (#925).

## Cerradas por obsoletas o sustituidas
#754, #757, #766, #770, #780, #802, #804, #810, #813 (el arreglo ya estaba en `main` o la PR tenia conflictos), #759 y #903 (sustituidas por #906 y #908), #764 y #803 (por #919), y #756, #763, #769, #782, #785, #786, #789, #791 y #806 (por #918).

## Pendiente de decision
- #788: quita `nl-subscribed` de la pagina de gracias (cambia el comportamiento del popup).
- #795: sustituye el modal de compra por enlaces directos de afiliado a Amazon (incluida la fila "Librerias").
- #765: politica de indexado de entradas del registro que comparten `sourceFile` (haria indexable `libros/index.html`).
- #790: el panel del asistente deja de ocultarse hasta estar listo.
- #783, #787, #792, #812: su test tambien falla con su propio arreglo.
- #755: cerrada; anade una segunda CSP a `offline.html`, que ya la tiene por #906. Los lotes nuevos del pipeline (#907, #923) y #817 (rendimiento del reflow) no se han tocado.
- Ruido de CI externo: `check-links` (HTTP 000 a servidores externos) y CLS inestable de `prensa.html @ 768`; ambos pasaron al relanzar una vez.
