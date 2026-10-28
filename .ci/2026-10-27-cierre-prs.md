# Cierre de PRs pendientes (2026-10-27)

Sin secretos. Todo por PR, sin `--admin` ni saltar la CI. «Comprobado» = ejecutado en este entorno o con CI en verde; «lanzado» = pendiente de que lo confirme una ejecución posterior.

## Fusionado

| Grupo | PRs fusionadas | Originales cerradas como incorporadas |
|---|---|---|
| Causas de los lotes qa-gpt en rojo | #938 (hashes CSP de páginas sueltas + contraste de `offline.html`), #939 (presupuesto `shell-v1`), #940 (aria-label del radar), #942 (token dorado de findability) | #927 #929 #932 #933 #934 #935 #936 #937 |
| Código del pipeline | #941 (en `automation/qa-gpt`: log del fallo, `sin_log`, pistas, relanzado de cancelados) | — |
| PRs del titular y del pipeline | #945 (consentimiento, sessionStorage, área táctil), #788 (`nl-subscribed`), #795 (degradación progresiva de Samuel), #923, #907, #943, #928 | #765 |
| Tests y gates | #947 (8 contratos V1), #948 (13 comprobaciones en el gate), #949 (esperas observables), #950 (9 comprobaciones endurecidas) | #574 #575 #586 #592 #598 #599 #604 #605 · #606–#612 #614–#616 #619 #621–#623 · #584 #589 #590 #591 · #618 #620 #624–#631 |
| Documentación | #951 (18 documentos), #593 (skill `pr`) | #528 #576 #577 #613 #666 #667 #670 #691 #693 #694 #698 #708–#714 |
| Investigación con código | #952 (atlas), #953 (lecturas + auditoría de enlaces), #954 (validadores de donaciones), #955 (copias de mapas), #956 (identidad), #957 (lecturas, sin cablear) | #671 #673 #675 #677 #678 #679 · #680 #718 · #700 #701 · #668 · #600 |

## Cerrado sin fusionar

- #781, #771: el main ya contenía el cambio.
- #790: su test ya pasaba sin el cambio.
- #812, #792, #787, #783: su propio test sigue fallando con el cambio; ramas conservadas.
- #817: el reflow ya se fragmenta en 8 jobs; reaplicar la concurrencia tocaba el harness que gatea todas las PRs.
- #683: se incorporaron solo los módulos nuevos (#957); el cableado en producción choca con el catálogo rediseñado.

## Comprobado

- Cada PR consolidada se aplicó sobre el main actual, sus tests nuevos pasaron en local y su CI salió en verde antes de fusionar.
- Pasan en local: `build-site-shell.py --check`, `check-asset-versions.py`, `build-pagefind-index.py --check`, `check-performance-budgets.py --check`, los 13 scripts añadidos al gate, el contrato de Samuel/compra, el QA de identidad y el flujo DOI de newsletter (tests de cliente, de validación y de worker).
- Suite de qa-gpt en Linux: 769 tests; fallan 6 que ya fallaban por rutas, PID y locks de Windows.

## Fallos y correcciones durante la ronda

- `check-copy-tildes` marcaba código de terceros (`research/vendor/kdbush`) cuando el gate pasó a ejecutarlo: ahora ignora `vendor/`.
- Tests de #680 sin poder ejecutarse (ruta `parents[2]`) y `SyntaxError` en `reading_free_prices.py`: corregidos.
- `qa/samuel-book-fragment-browser.mjs` contaba como duplicados los enlaces de Amazon que añade #795: ahora excluye los disparadores del modal.
- Versiones de assets y hashes CSP de #945 sin actualizar: subidas y regeneradas.
- Fallos de infraestructura, relanzados una vez: `check-links` (reset de conexión externo), `smoke` y `consent-banner-positioning-qa` (cuelgue de apt/Playwright) y un 503 transitorio de producción en el audit de 4ca6a77.

## Lanzado, pendiente de confirmar

- `Post-deploy deep audit` de los últimos commits de main (b2dd41b, 9bd7c13): en cola o en curso al escribir esto. `Live production PWA QA` salió en verde en b2dd41b y 9bd7c13; el resto de merges de la ronda solo añade ficheros inertes.
- `newsletter-popup-persistence-browser` no cupo en el tiempo local; lo cubrió la CI de #788.

## Pendiente de decisión del titular

- #617 (hook `guard-main`): bloquea `git merge`, `gh pr merge`, `gh api PUT .../merge`, `checkout -B` y `reset --hard` para cualquier agente. No se ha fusionado porque contradice el flujo actual de fusiones por agente.
- #946: PR diaria del bot del catálogo de lectura; se regenera sola.
- Cableado de modos de precios (#683): rehacer sobre el catálogo actual cuando se decida el modo.
- Fuera de la nube: cambios locales sin subir, `qa/_tmp_probe.mjs`, logs locales y estado de INICIAR/EJECUTAR.
