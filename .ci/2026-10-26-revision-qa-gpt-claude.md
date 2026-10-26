# Revision humana asistida de los lotes qa-gpt (2026-10-26)

Constancia de la revision de las PRs de riesgo medio que el pipeline dejo para revision, y de las PRs de lote cerradas por CI roja. No sustituye al informe de la noche (`informe-qa-gpt-noche-2026-10-26`), que no esta en `main` ni en `automation/qa-gpt`.

## Fusionadas
- #886 (enlace nativo en `offline.html`), #887 (enlace Eventos -> ficha de Aranjuez), #751 y #753 (lecturas: JSON-LD sin fixture y fechas en espanol), #896 (14 tests de proteccion).
- Recuperadas en PRs nuevas: #904 (QA), #906 (CSP de `offline.html` y `video-ios-test`), #908 (presupuesto de `catalogue-runtime`), #910 (club, eventos, radar y Pagefind).

## Causas de los rojos de los lotes
- `browser-qa` "Guardar ficha" `tabindex=-1`: `qa/tools-events-memory-browser.mjs` no admitia los submit `.sr-only` que #868 saco del Tab a proposito. El workflow solo corre en PRs que tocan sus rutas, asi que #868 no lo ejecuto. Arreglado en #904. El `curl: (7)` del log es el primer intento del bucle de espera, no el fallo.
- `performance-budget`: #903 declaraba 45189 B / 2 requests; lo real son 63497 B / 3 (el CSS carga una fuente). Arreglado en #908.
- `radar HTML drifted from builder`: #884 cambiaba `data/radar-opportunities.json` sin regenerar `convocatorias-escritores/`. Arreglado en #910.
- Hash CSP de #759 obsoleto tras #886 (habria bloqueado los estilos de la pagina offline). Recalculado en #906; el QA `pwa-offline` inyecta su hoja de estres con `bypassCSP`.

## Cerradas por obsoletas o duplicadas
#754, #757, #766, #770, #780, #802, #804, #810, #813 (el arreglo ya esta en `main` o la PR tenia conflictos), #759 y #903 (sustituidas por #906 y #908).

## Pendiente
- #764 y #803 (validas, con conflictos: requieren rebase), #806 (aserciones Lighthouse `http-status-code`, requiere CI propia).
- Borradores #755, #756, #763, #765, #769, #782, #783, #785 a #792, #795 y #812: sin revisar.
- Ruido de CI externo: `check-links` (HTTP 000 a servidores externos) y CLS inestable de `prensa.html @ 768` en `identity-public`; ambos pasaron al relanzar.
