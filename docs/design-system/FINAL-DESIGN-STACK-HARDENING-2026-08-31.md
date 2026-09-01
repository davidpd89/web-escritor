# Cadena DISEÑO — hardening transversal y cierre de pila

Fecha: 2026-08-31
Estado: hardening final en curso
Base de esta rama: `design/offline-pwa-visual-unification-2026-08-31` (#290)

## Objetivo

Cerrar de forma auditable dos deudas detectadas durante la segunda pasada de las PR de diseño sin reescribir ramas intermedias ya certificadas:

1. evidencia visual heredada con imágenes lazy que no siempre se decodificaban explícitamente en capturas especiales;
2. reconciliación operativa del drift de la pila a partir de #265 respecto al HEAD final de #264.

Esta PR no es un nuevo rediseño. No debe introducir cambios de producción salvo que un QA nuevo descubra un defecto reproducible.

## Cobertura del inventario

Tras cruzar `sitemap.xml`, el árbol público y las PR de diseño, todas las URLs indexadas actuales tienen una familia de revisión asignada dentro de #163–#290.

Las superficies noindex/utilitarias relevantes también tienen owner de revisión:

- Findability/404/gracias: #283;
- Asistente: #284;
- Lectores beta: #285;
- guía imprimible Club Samuel: #286;
- Legal: #287;
- Accesibilidad: #288;
- `/ai/`: #289;
- Offline/PWA: #290.

No abrir PR visual por defecto para fixtures/staging/checklists internos o recursos noindex sin decisión de publicación.

## Segunda pasada — resultados

### #278 Ferias

Ya endurecida en su propia rama antes de abrir las nuevas familias:

- nomenclatura QA corregida a `visual-system contract`;
- `target Madrid` y no-JS cargan/decodifican las ocho imágenes lazy;
- 11/11 workflows verdes en `1ba8483b019b8d307a2194ac96d0f58e0c6a2ba7`.

### #277 Prensa

Producción y print funcional: correctos.

Deuda detectada: las 15 capturas principales llaman a `loadDocumentaryImages()`, pero la captura no-JS no fuerza la decodificación de retrato, galería y mockups antes de generar evidencia.

### #276 Eventos

Producción: sin defecto visual objetivo nuevo.

Deuda detectada: la foto documental se carga/decodifica en los artboards principales, pero no explícitamente antes de la captura no-JS.

### #275 Premios

Sin defecto objetivo pendiente. Separación factual/visual entre reconocimientos, trayectoria y recepción correctamente protegida; aislamiento de tokens específico.

### #274 Autor

LCP/portrait principal, CLS, seams, schema y aislamiento: protegidos.

Deuda detectada: la imagen documental lateral se valida por existencia, pero no se fuerza su decodificación antes de las capturas principales/no-JS.

### #273 Convocatorias

Sin deuda de reloj real. `tests/test-radar-freshness-real-clock.py` usa `date.today()`, demuestra que una oportunidad publicada con 31 días sin verificar falla y que una verificada hoy pasa, y finalmente valida el repositorio actual mediante `checker.check_radar()`.

### #272 Editoriales / #271 Metodología

Sin fuga renderizada nueva. `assets/editoriales.css` alberga primitivas compartidas, Metodología y directorio bajo scopes estructurales distintos. Es deuda de mantenibilidad baja, no bug actual. No separar la hoja salvo conflicto real durante #281 fichas individuales.

### #270 Herramientas / #269 Cuaderno

Hubs técnicamente cerrados. Las superficies excluidas se cubren ahora mediante #280 y #279 respectivamente; no reabrir los hubs para ampliar alcance.

### #268 Club Samuel / #267 Noveris / #266 capítulo Samuel

Aislamiento, cross-engine, contenido/schema, CLS/reflow y lectura están bien protegidos. La guía imprimible queda separada en #286.

### #265 Samuel — bloqueo operativo de pila

La rama #265 fue creada desde el antiguo HEAD de #264 `746c75a...`, mientras #264 terminó en `a2b075f6cf6ba4cf2077b140ea2219d4772c287e`.

#264 sí fue reconciliada con el #205 final y revalidó 11/11 workflows. El delta tardío incluye hardening real en `assets/v1-manecillas-fixes-v8.css` y `qa/manecillas-scope-isolation.mjs`; no es documentación-only.

#265 y sus descendientes históricos no contienen esos commits en su propia historia y su CI histórico no certifica el HEAD combinado con el padre final.

Esto no implica necesariamente un conflicto textual ni obliga a reescribir ahora toda la historia. Implica que la integración debe hacerse de forma secuencial y cada descendiente debe revalidarse contra la base ya integrada.

### #264 / #205 / #174

- #264: reconciliada con #205 final, HEAD `a2b075f...`, 11/11 verde.
- #205: HEAD `464d307...`, gates actuales verdes.
- #174: nació exactamente del HEAD final de #163 conocido y no presenta un drift equivalente documentado.

### #163 HOME

No se modifica desde esta PR. Sigue existiendo un bloqueo manual real ya documentado: intro inicial congelada/primer frame en iPhone Safari físico. Debe resolverse/revisarse en #163, no desde el hardening de cola.

## Corrección de diagnóstico factual — #289 / Manecillas

Una primera lectura de la fecha `2026-09-03` llevó a interpretar como inconsistencia la redacción `published` / `Publicada el 3 de septiembre de 2026` antes de esa fecha. Esa interpretación queda descartada tras revisar la autoridad canónica completa.

`editorial-facts.json` contiene una decisión editorial explícita del 20/08/2026, autorizada por David y deliberadamente independiente del calendario:

- `statusBeforePublication: "published"`;
- `statusFromPublicationDate: "published"`;
- el copy público autorizado mantiene `Publicada el 3 de septiembre de 2026` también antes del 03/09;
- `purchaseUrl` permanece `null` y la disponibilidad comercial se gobierna por separado.

`tests/test-machine-authority.py` refuerza exactamente ese contrato: exige que el press-kit mantenga `status: published` y que los estados antes/después de la fecha sigan siendo `published`.

Por tanto, la propagación de ese wording a `/ai/`, `llms.txt`, `llms-full.txt`, press-kit, HOME, Libros, Autor, Prensa y la ficha de Manecillas es coherencia con la fuente de verdad, no drift accidental.

Regla de cierre:

- no convertir el estado a `forthcoming`, `scheduled`, `se publica` ni equivalente por fecha del runner;
- no inventar retailer, `Offer` ni disponibilidad mientras no exista URL comercial verificada;
- cualquier QA de #289 debe validar coherencia con `editorial-facts.json`, no sustituir la política editorial por una inferencia calendárica.

La sección previa del contrato de #289 que trataba esta redacción como bloqueo factual queda superseded por la corrección registrada en el body de #289 y por este documento de cierre.

## Hardening implementado aquí

`qa/design-evidence-hardening.mjs` añade cuatro casos suplementarios:

1. Autor 1440 con JS — retrato principal + imagen documental lateral;
2. Autor 390 sin JS — ambas imágenes;
3. Eventos 390 sin JS — fotografía documental de Madrid;
4. Prensa 390 sin JS — retrato, galería y ambos mockups.

Cada imagen:

- se lleva al viewport mediante `scrollIntoViewIfNeeded()`;
- espera `load` si procede;
- ejecuta `decode()` cuando está disponible;
- exige `naturalWidth > 0` y `naturalHeight > 0`;
- se registra en JSON junto con `currentSrc`/`loading`;
- se captura solo después de decodificar;
- mantiene cero overflow.

Workflow: `.github/workflows/design-evidence-hardening.yml`.
Artefacto: `design-evidence-hardening`.

HEAD certificado antes de esta corrección documental: `859b1d167b6c87e46ddbf064a13254857013cf7e`, 7/7 workflows `success`, incluido `Design evidence hardening` run `33379847958`, artifact digest `sha256:23b9616ea638c3a35fb4bc390fc51fbddd0ee5eb8286a25edb06dd6aa5278d7f`.

La corrección de diagnóstico de este commit es documental; el nuevo HEAD debe volver a completar sus workflows antes de considerarse certificado.

## Procedimiento obligatorio de reconciliación antes de merge

No hacer un rebase masivo de 25 ramas.

Integrar en orden y, en cada escalón:

1. mergear únicamente la PR padre cuando esté realmente aprobada;
2. retargetear la siguiente PR a `main`;
3. comprobar el merge-base y revisar que el diff resultante corresponda solo al alcance propio de esa PR;
4. si GitHub construye una combinación limpia, actualizar/reconciliar la rama solo cuando sea necesario para obtener un HEAD exacto testeable;
5. ejecutar todos los workflows aplicables sobre esa combinación exacta, no reutilizar el verde histórico;
6. revisar los contratos de aislamiento de la familia;
7. no continuar al siguiente descendiente si falla un gate;
8. repetir hasta la cola.

Punto de atención principal al llegar a #265:

- demostrar que las correcciones tardías de #264 están presentes en el resultado combinado;
- volver a ejecutar Samuel ecosystem, Manecillas isolation, Cross-engine, Pa11y, Reflow y Lighthouse relevantes;
- comprobar que el diff propio de Samuel no vuelve a modificar Fragmentos/Manecillas de manera accidental.

Después, el mismo principio se aplica a #266–#290 y a esta PR final.

## Bloqueos / comprobaciones de cierre conocidos fuera de esta PR

- #163: Safari/iPhone físico, intro.
- #286: verificar el baseline real de robots de la guía imprimible antes de implementar su contrato visual.
- #287: verificar el posible drift entre el texto de Privacidad y el consentimiento real del newsletter antes de decidir si requiere corrección funcional separada.
- #290: demostrar upgrade real del service worker/cache al cambiar `offline.html`.
- revisión física global de dispositivos según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

#289 **ya no figura como bloqueo temporal**: el wording `published/publicada` es una decisión canónica confirmada y protegida.

## Definition of Done de esta PR

- smoke suplementario de evidencia verde;
- artefacto revisable con las cuatro capturas y JSON sin failures;
- CI general sin regresiones;
- ningún cambio de producción introducido por conveniencia;
- procedimiento de reconciliación documentado;
- diagnóstico factual #289 corregido sin alterar la política editorial autorizada;
- PR Draft, abierta y sin merge hasta que su base #290 y toda la pila previa estén integradas/revalidadas en orden.
