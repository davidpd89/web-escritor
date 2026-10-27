# Triaje de PRs qa-gpt (2026-10-27)

Sin secretos. Todo por PR, sin `--admin` ni saltar la CI.

## Lotes cerrados en rojo: causas reales (ninguna era el puerto 4173)

| Causa | Lotes | Recuperado en |
|---|---|---|
| Hash CSP de `offline.html` sin regenerar al tocar su CSS | #927, #929, #932, #936 | #938 (el generador del shell ya recalcula y comprueba los hashes de script y estilo) |
| Detector de presupuestos sin recapturar `shell-v1` | #934, #935 | #939 |
| Página generada editada a mano | #933 | #940 |
| Contraste del token dorado de findability | #934 (parte), #937 | #942 |

## Código del pipeline (`automation/qa-gpt`)

- #941 fusionada: `Gh.log_failed` pide el log de cada job fallido por la API si `--log-failed` viene vacío; el supervisor no llama a Claude sin log útil (avisa con `ATENCION`, resultado `sin_log`, reintento a la hora sin gastar intentos); los lotes de 1 corrección en rojo llevan una pista de la causa conocida; los checks solo `CANCELLED` se relanzan una vez.
- Verificado con la rama que ya incluía 571c07a (reintento de `registrar_test`): solo fallan los 5 tests que dependen de Windows y ya fallaban antes.

## PRs qa-gpt abiertas

| PR | Resultado | Motivo |
|---|---|---|
| #928 | fusionada | fecha visible de privacidad coherente con el historial |
| #923 | fusionada | 8 tests de protección; pasan en main y en el árbol fusionado; su rojo era la frescura del radar, ya resuelta |
| #907 | fusionada | endurece el sitemap; sus tests fallan en main y pasan con el cambio |
| #781, #771 | cerradas | el main actual ya contiene el cambio (mismo árbol) |
| #790 | cerrada | su test ya pasa en main; el cambio muestra el panel antes de que el JS lo prepare |
| #812, #792, #787, #783 | cerradas | su propio test sigue fallando con el cambio; ramas conservadas |
| #765 | cerrada | sustituida por #943, fusionada (libros/index.html fuera del índice de Pagefind) |
| #788, #795 | abiertas, decisión del titular | #788 deja de marcar `nl-subscribed` al visitar la página de gracias (los suscriptores reales volverían a ver el popup); #795 cambia el destino sin JS de «¿Dónde comprar?» a Amazon con afiliado |

## Fuera de alcance de la nube

Cambios locales en `C:\GIT\web-escritor-qa-gpt` (si siguen sin commitear), `qa/_tmp_probe.mjs`, logs locales y el estado de INICIAR/EJECUTAR.

## Main

`Live production PWA QA` en verde en 9b0368e, 3e973ce y 142217e. `Post-deploy deep audit` en verde en 3e973ce; en 142217e salió `cancelled` (lo sustituye la ejecución del merge siguiente, d3b75b3, #907), por lo que queda por confirmar la ejecución de d3b75b3.
