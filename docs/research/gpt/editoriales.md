# Investigación de GPT — editoriales, sellos y contactos

**P0 · DRAFT · NO MERGEAR.** Coordinación: [#691](https://github.com/davidpd89/web-escritor/pull/691). Dependencias: catálogo [#687](https://github.com/davidpd89/web-escritor/pull/687), investigación de proveedores [#680](https://github.com/davidpd89/web-escritor/pull/680), auditoría de sellos [#683](https://github.com/davidpd89/web-escritor/pull/683).

## Gap exacto (revisado 22/10/2026)

En `main`, `data/editoriales.json` contiene **150** editoriales con fuentes, web y estado de recepción (72 open, 45 closed, 26 unknown, 7 indirect); solo **54** incluyen un correo específico de manuscritos. El constructor `scripts/build-editoriales.py` genera fichas y alerta de verificaciones antiguas. No hay captación universal automática ni actualización fiable continua de estado/contactos.

La **PR #687, fusionada el 22/10/2026**, introdujo en `main` `data/reading-publishers.json`: **11 sellos** descubiertos por libros de Penguin, con URL bibliográfica y ficha de sello. Son **identidades bibliográficas**, no pruebas de que reciban manuscritos. No deben fusionarse semánticamente con el directorio de recepción sin resolver aliases, grupos y contactos.

## Resultado perseguido

1. **Un registro canónico de entidades editoriales**, con relación sello → editorial → grupo y alias; tabla de procedencias por atributo. `editoriales.json` puede seguir como proyección de directorio y `reading-publishers.json` como proyección bibliográfica: evaluar migración sin romper URLs ni la #687.
2. **Descubrimiento incremental sin rastreos agresivos**: fuentes oficiales en España, sellos extraídos de libros, listas y feeds autorizados por editor; incorporar cambios como *candidatos* con evidencia. No asumir que «todas las editoriales existentes» tienen datos públicos completos; incluir estado de cobertura y no indexar fichas sin sustancia.
3. **Contactos separados**: web y contacto general públicos, oficina/prensa/manuscritos solo si fuente oficial lo dice. No recoger emails de personas físicas sin base de uso; comprobar legislación y aviso legal. Nunca generar correo por patrón de dominio ni interpretar «sin respuesta» como «cerrada».
4. **Recepción de manuscritos dinámica**: `open/closed/indirect/award_only/unknown`, URL primaria, método, requisitos, fecha comprobada, siguiente revisión, historial. Un estado sin fuente válida o envejecido pasa a «por verificar»; no exponer instrucciones como actuales.
5. **Relaciones web**: ficha de editorial → libros nuestros/autores relacionados; ficha de libro → sello/grupo; navegación diferenciada «Catálogo editorial» y «Envío de manuscritos» con facetas y canonical correctos.

## Primera fuente y límite

[Ministerio de Cultura — base de datos de editoriales](https://www.cultura.gob.es/cultura/libro/isbn/base-de-datos-de-editoriales.html) incluye editoriales activas e históricas, autores-editores y entidades ocasionales. [Datos.gob.es](https://datos.gob.es/es/catalogo/e05234201-base-de-datos-de-editoriales) publica una **distribución XHTML**, no una API pública JSON garantizada ni permiso automático de scraping. Primer paso: confirmar consulta/exportación permitida y condiciones aplicables; si no, pedir feed autorizado, no sortear barreras. [DILVE/ONIX](https://web.dilve.es/onix/estandar-versiones-editeur/) puede aportar metadatos, pero acceso a feeds no garantizado.

[RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) (MIT, librería mantenida): candidato para *sugerir* alias, jamás auto-unificar «Planeta», «Editorial Planeta», sellos y personas homónimas por similitud.

## Pasadas de trabajo (orden)

- **E1 COMPLETADO (auditoría de los JSON de main y #687, sin ejecutar código del proyecto):** no hay coincidencias exactas ni de nombre normalizado entre los 11 sellos del catálogo y las 150 editoriales del directorio; 35 de los 55 libros de #687 enlazan a fichas del directorio, todas con `status=unknown`; otros 20 enlazan a 9 de los 11 sellos exclusivamente bibliográficos. **Beascoa y Montena** tienen ficha de sello/fuente, pero cero libros publicados asociados en esa rama; revisarlas como huérfanas antes de indexarlas. Los estados de manuscritos no se pueden inferir de esta distribución. No he encontrado colisiones de nombres normalizados dentro de las 150 editoriales. Estos recuentos son instantáneas de #687, **no** de `main`.
- **E2 INVESTIGADO / RUTA ELEGIDA:** consultar límites del ISBN y DILVE, descartando la copia de resultados ISBN sin autorización explícita; fuente estructurada inicial **Wikidata CC0**, solo para proponer entidades y webs. Se ha creado adaptador offline de Wikibase JSON y 9 pruebas escritas sin ejecutar. Pendiente piloto con QIDs reales contrastados, confirmación de permisos de webs editoriales y petición de autorización/volcado a Agencia ISBN para ampliar cobertura. Véase hallazgo fechado abajo.
- **E3 CÓDIGO PREPARADO:** `scripts/research/gpt_editoriales_reconcile.py` ya compara, en modo solo lectura y con ficheros suministrados explícitamente, slugs, alias sugeridos, datos obsoletos, fuentes de ficha, registros sin libros y enlaces rotos. Devuelve JSON para revisión sin filtrar correos ni escribir `data/editoriales.json`. **No probado todavía**; #692 no copia los 11 sellos porque ya residen en `main`. El próximo estudio E6 podrá usarlos sin importar otra rama.
- **E4 INVESTIGACIÓN Y CÓDIGO PREPARADOS, SIN EJECUTAR:** se revisó una muestra de **15 entidades reales** (13 sellos/editoriales y 2 grupos), con 6 QIDs localizados (uno es Bruguera histórico y no se debe unir al sello actual) y 18 observaciones de contactos tipificados. Documentación y resultados en [`editoriales-e4-resultados-2026-10-22.md`](editoriales-e4-resultados-2026-10-22.md). Se preparó `gpt_editoriales_contact_evidence.py` con allowlist independiente, caducidad y conflictos; **15 pruebas sintéticas adicionales sin ejecutar**. Las 11 pruebas de E3 tampoco se han ejecutado.
- **E5 DISEÑO Y CÓDIGO PREPARADOS, NO EJECUTADOS:** revisar [informe E5](editoriales-e5-integracion-2026-10-22.md). Confirmado en el código real que el bot diario ya tiene exclusión de PR pendientes, allowlist, controles de CI y concurrencia; la allowlist de #687 **no incluye** `data/editoriales.json`. Se propone **un solo orquestador con dos carriles**: bibliografía verificada → bot de libros actual; contacto/recepción → revisión humana y PR separada no automática. Preparado `scripts/research/gpt_editoriales_review_plan.py` y **21 casos de prueba sintéticos adicionales sin ejecutar** (57 en los cuatro módulos).

**Criterio de salida:** demo offline reproducible, cero duplicados publicados, contactos con procedencia, ninguno de los 150 estados alterado sin verificación y coste de servicios externos 0 €. Si no se permite usar una fuente, se documenta NO-GO y alternativa.

**No ejecutado:** ninguna prueba, extracción masiva, edición de datos públicos o publicación.


## Hallazgos técnicos de esta pasada — 22/10/2026

**Separación de hechos:**
- `status` en `data/editoriales.json` informa sobre la **recepción de manuscritos**, no si la editorial sigue publicando. `status=unknown` significa que no tenemos fuente comprobada sobre manuscritos, **no** que la editorial esté inactiva.
- `editorial_slug` en un libro enlaza al **directorio de manuscritos** (`/editoriales/<slug>/`). `editorial_catalogo_slug` enlaza al **sello bibliográfico del catálogo** (`/recomendaciones/editoriales/<slug>/`). El informe marca libros con ambos o sin ninguno; no sustituir uno por otro.
- El índice de nombres registra **cero colisiones internas por normalización simple** en 150 entradas y **cero equivalencias** entre los 11 sellos nuevos y nombres exactos del directorio. Esto no demuestra que las empresas sean distintas: nombres comerciales, alias, sucesiones y estructuras societarias requieren evidencia externa.

**Ministerio de Cultura/ISBN:** [directorio público](https://www.cultura.gob.es/cultura/libro/isbn/base-de-datos-de-editoriales.html) permite consultar editores activos, no activos, prefijo ISBN y localidad; también incluye autores-editores y organismos, por tanto **no equivale** a «todas las editoriales profesionales actuales». La ficha [datos.gob.es](https://datos.gob.es/es/catalogo/e05234201-base-de-datos-de-editoriales) lista **solo distribución XHTML** y los comentarios piden un formato abierto. La [API de datos.gob.es](https://datos.gob.es/es/accessible-apidata) consulta **metadatos del catálogo**, no proporciona una API confirmada de las filas de editoriales. No implementar scraping de formularios, POST repetitivo ni sortear robots para convertirlo en un feed.

**Licencia y atribución:** el [aviso legal del Ministerio de Cultura](https://www.cultura.gob.es/comunes/aviso-legal.html) autoriza de forma general la reutilización de información pública sometida a esas condiciones, con obligación de **citar origen, respetar significado y conservar fecha/condiciones**. No autoriza sin más fuentes de terceros con otras restricciones ni da permiso para saturar el buscador. Verificar si los datos concretos de Agencia ISBN se rigen por aviso específico y, antes de extraer masivamente, solicitar exportación o acceso regulado. En fichas atribuidas: «Origen de los datos: Ministerio de Cultura» y fecha si disponible.

**Opciones técnicas revisadas:**
- [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz), licencia MIT: útil para **proponer** coincidencias a revisar si crece el directorio. Para el piloto basta normalización con `unicodedata` y `re` de Python; por eso **no se añade dependencia ni copia de código externo**.
- [onixcheck](https://github.com/titusz/onixcheck), licencia Apache-2.0: valida ONIX 2.1/3.0/3.1, **no** descarga bases de datos ni proporciona contactos. Candidato para una fase futura si obtenemos un feed ONIX autorizado; no instalar antes.
- [DILVE](https://web.dilve.es/calidad-de-metadatos-2/metadatos/precio/) es infraestructura editorial con metadatos y precios; **no** asumir un feed público gratuito de nombres y contactos.
- [Open Library](https://openlibrary.org/developers/api) desaconseja usar la API para descargas masivas; ofrece [dumps mensuales](https://openlibrary.org/developers/dumps), útiles sobre todo para obras/ediciones y autores. No convierte sus nombres de editoriales en contactos corporativos verificados.
- [Wikidata](https://www.wikidata.org/wiki/Wikidata:Data_access/es) puede ayudar en identidad de grupos y sellos, con limitaciones de peticiones. **No** usarlo como fuente del estado de manuscritos ni correos.

**Contrato de contacto pendiente:** `general_public`, `submissions_public` y `press_public` deben ser canales **distintos**, con `source_url`, fecha, caducidad y decisión de publicación por campo. No inferir un correo de patrón `info@` o `manuscritos@`. Si se desconoce, mostrar web oficial; si caduca la prueba, pedir nueva comprobación. El descubrimiento podrá ser automático; la **aceptación y publicación del contacto** requiere una fuente primaria fiable y política de datos personales.

### Uso del prototipo (NO ejecutar desde la CI ni producción)

El conciliador necesita **tres ficheros explícitos**, ya disponibles en `main` tras fusionar #687. Su ejecución requerirá autorización expresa; no se ha realizado:

```sh
python scripts/research/gpt_editoriales_reconcile.py \
  --directory data/editoriales.json \
  --catalogue-publishers data/reading-publishers.json \
  --books data/reading-catalogue.json \
  --as-of 2026-10-22
```

Salida: JSON en stdout con recuentos, colisiones, casos huérfanos y `imprint_candidates` con `decision=review_*|catalogue_only|quarantine_source`. Solo sugerencias, **jamás fusiones, cambios de status o alta directa**. Los datos deben provenir del **mismo commit de `main`** para evitar falsos errores referenciales. La rama no añade ni altera jobs, workflows ni datos públicos.

**Siguiente acción recomendada — E2/E4:** obtener permiso o export de la base ISBN; luego preparar 20 coincidencias reales manualmente y probar la validez/atribución de contacto antes de automatizar una sola ficha. Se mantiene el coste objetivo cero.


## E2 — vías de descubrimiento contrastadas (22/10/2026)

| Fuente y prueba primaria | Gratuidad y formato real | Qué permite / qué NO | Decisión |
|---|---|---|---|
| [Ministerio, directorio de editoriales](https://www.cultura.gob.es/cultura/libro/isbn/base-de-datos-de-editoriales.html) + [ficha datos.gob.es](https://datos.gob.es/es/catalogo/e05234201-base-de-datos-de-editoriales) | Consulta web XHTML, actualizaciones diarias; **no** CSV/JSON/endpoint de filas verificado | El [Ministerio aclara expresamente (20/07/2026)](https://datos.gob.es/es/catalogo/e05234201-base-de-datos-de-libros-editados-en-espana) que no es titular ni verifica los datos cedidos por la **Agencia del ISBN**, de carácter privado. Su aviso legal general **no acredita una licencia de explotación masiva de los registros de tercero** | **HOLD** para ingestión masiva; sí consulta manual puntual para contraste |
| [Agencia Española del ISBN](https://www.cultura.gob.es/cultura/libro/isbn/informacion.html) | Titularidad y derechos de los datos deben confirmarse | Contacto público oficial **agencia@agenciaisbn.es**; solicitar explícitamente formato/actualizaciones, autorización de redistribuir campos y límites, precio 0 € o tarifa real. **No se ha contactado ni obtenido permiso** | **PENDIENTE DE PERMISO**, fuente preferida de expansión nacional si autorizan |
| [Registro Global ISBN](https://grp.isbn-international.org/content/using-register/358) + [condiciones](https://grp.isbn-international.org/node/6) | Consulta básica pública; registro gratis para contactos completos; no API masiva autorizada hallada | **Prohíbe expresamente almacenar, republicar y distribuir resultados de búsquedas, incluso registrándose**; permiso por escrito si se quiere reutilizar. No utilizar cuenta gratis como «API de contactos» | **NO-GO** de importación/redistribución sin licencia escrita |
| [DILVE, FAQ](https://web.dilve.es/asistencia-2/preguntas-frecuentes/) | **Sí existe API HTTP** de descarga y extracciones automáticas ONIX, pero exige **alta y derechos de usuario/entidad**; tarifa/licencia para nuestro uso no confirmadas | Sirve principalmente para datos de libros y editoriales participantes, no para contactos de recepción de manuscritos. No afirmar que es API pública gratuita | **CONDICIONAL**, pedir condiciones si interesa ampliar libros |
| [Wikidata, licencia CC0](https://www.wikidata.org/wiki/Wikidata:Licensing) + [mecanismos de acceso](https://www.wikidata.org/wiki/Wikidata:Data_access/es) | Estructura JSON, `Special:EntityData/Qxxx.json` o `action=wbgetentities`; datos estructurados CC0, acceso público; API para **pequeños grupos**, dumps para escala | [P856 web oficial](https://www.wikidata.org/wiki/Property:P856), [P749 organización matriz](https://www.wikidata.org/wiki/Property:P749), [P17 país](https://www.wikidata.org/wiki/Property:P17), [P31 clase](https://www.wikidata.org/wiki/Property:P31). **Solo candidatos**: P856 puede contener webs antiguas/secuestradas y Wikidata no verifica contactos comerciales ni manuscritos | **PILOTO E2 APROBABLE TÉCNICAMENTE**, revisión humana y verificación web antes de publicar |
| [Open Library API](https://openlibrary.org/developers/api) / [dumps](https://openlibrary.org/developers/dumps) | API JSON gratuita **no para extracción masiva**; dumps bibliográficos gratuitos pero muy voluminosos | Los campos de editorial en ediciones son **texto bibliográfico** y no acreditan web, entidad jurídica o correo válido | **FUENTE DE LIBROS**, no directorio de contactos |

### Arquitectura acordada en investigación (NO ACTIVADA)

1. **Semilla**: nombres y sellos de los libros admitidos en el único pipeline vigente + catálogo local del directorio actual; opcional Wikidata para candidatos y relaciones de grupo con QID. No rastrear alfabéticamente bases completas sin permiso.
2. **Identidad**: nombre/alias/URL/QID con procedencia. Coincidencia de nombre o dominio = `manual_review_required`, no alta automática. Un grupo comparte dominio con sellos distintos; un sello puede tener nombre propio. La empresa matriz no hereda estado de recepción.
3. **Contactos**: visitar únicamente URLs oficiales autorizadas, con presupuesto y robots verificados por proveedor, capturar **referencias por campo** y fecha; general/prensa/manuscritos separados. Se requerirá verificar la **idoneidad del contacto** y un tratamiento de datos personales conforme antes de publicar. No copiar resultados ISBN/GRP como alternativa.
4. **Datos dinámicos**: `status=unknown` mientras no conste declaración reciente y explícita de recepción. La caducidad no equivale a «closed»; se muestra «por verificar». Cambio de estado exige evidencia nueva y registro reversible, no extracción por palabras aisladas.
5. **Publicación**: solo candidatos aprobados, en el **único** writer del catálogo tras resolver #687; sin workflow ni cron nuevos, sin activación en esta rama.

### Código preparado en E2, pendiente de ejecutar

- `scripts/research/gpt_editoriales_wikidata_candidates.py`: interpreta únicamente **snapshot Wikibase JSON suministrado**, sin HTTP; saca label, aliases, webs HTTPS candidatas (no páginas privadas, localhost ni dominios de ejemplo), identificadores de grupo/país/clase y posibles slugs del directorio por nombre/dominio. Descarta claims `deprecated` y prioriza `preferred`. **Siempre requiere revisión** y no genera correo ni estado de manuscritos. Una web P856 **no** se considera demostración de propiedad/control: se debe comprobar.
- `tests/test_gpt_editoriales_wikidata_candidates.py`: **10 pruebas sintéticas escritas y no ejecutadas**; validan URL sospechosa, prioridad y obsolescencia, homónimos, empresas que comparten dominio, y ninguna fusión/publicación automática.
- No se integra el módulo en el builder, no se realizan peticiones a Wikidata, no se copian ficheros externos protegidos y no se instala dependencia.

Ejemplo de acceso documentado, **para un piloto futuro con identificadores confirmados y respetando condiciones/cuotas**, no ejecutado en esta investigación:

```text
https://www.wikidata.org/wiki/Special:EntityData/Q<id-validado>.json
https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q<id-validado>&props=labels|aliases|claims&languages=es|en&format=json
```

El marcador `<id-validado>` debe sustituirse por un QID comprobado previamente: **no** es una URL literal ejecutable. El adaptador no acepta búsquedas por nombre y por diseño no inventa QIDs.

### Solicitud propuesta, todavía NO enviada

Destinatario oficial: **agencia@agenciaisbn.es** ([Ministerio de Cultura](https://www.cultura.gob.es/cultura/libro/isbn/informacion.html)).

> Asunto: Consulta sobre reutilización autorizada del directorio de editoriales españolas.
>
> Estamos desarrollando un directorio bibliográfico gratuito que enlaza libros, sellos y editoriales con sus sitios oficiales. Nos gustaría confirmar si la Agencia del ISBN ofrece un fichero descargable, API o feed incremental del directorio de editoriales; formatos, periodicidad y condiciones de acceso; y si sería posible almacenar, mostrar y actualizar nombres, web institucional y datos profesionales de contacto en fichas públicas, indicando atribución y fecha. También quisiéramos conocer tarifas, límites de peticiones y si hay condiciones especiales para entidades históricas o autores-editores. **No solicitamos datos privados.** Gracias.

Este texto **no representa autorización concedida ni una comunicación enviada**. No iniciar importación masiva mientras no haya respuesta/licencia aplicable.

### E4 realizada: consultar el informe enlazado y continuar E5

- Investigar **QIDs reales** de 10–20 sellos de catálogo, verificar correspondencia con fichas originales y cuantificar cobertura de Wikidata (`P856`, `P749`, `P17`, `P31`). Guardar solo un informe de fuentes, no nombres inferidos. Validar adaptador únicamente con datos autorizados, primero offline.
- Definir el **contrato de evidencia del contacto**, lectura de páginas oficiales con controles de licencia/robots y detección no ambigua de sección de manuscritos. Preparar pruebas sintéticas y cola manual.
- **No** avanzar a llamadas masivas a ISBN ni al Global Register: no existe permiso documentado de reutilización. Si recibimos autorización de Agencia ISBN, reevaluar esta decisión y documentar coste/condiciones antes de escribir el conector.


## Estado actual y próxima pasada (22/10/2026)

**E4 terminada**: [informe específico](editoriales-e4-resultados-2026-10-22.md). **E5 terminada como investigación y propuesta no ejecutada**: [diseño de integración E5](editoriales-e5-integracion-2026-10-22.md). #687 se ha **fusionado**; ya no es dependencia abierta. **E6.1/E6.2 documentadas y código preparado sin ejecutar.** Próximo paso E6.3: piloto offline de cinco candidatos y revisión de posibles errores; detalles al final del documento.


**Actualización de estado 22/10/2026:** #687 fusionada en `main` durante E5. `main` contiene 55 libros (35 enlazan al directorio, 20 a sellos exclusivos), 55 autores, 11 sellos y 150 editoriales. Los informes E1/E4 conservan su procedencia histórica de la rama #687; E6 debe usar **únicamente los datos de `main` del mismo commit**. #692 sigue DRAFT y sin tests ejecutados.

## E6.1/E6.2 — contrato por campo y comprobación con main (22/10/2026)

**Documentación principal:** [editoriales-e6-contrato-2026-10-22.md](editoriales-e6-contrato-2026-10-22.md) y [baseline auditable de `main`](editoriales-e6-baseline-2026-10-22.json), commit `72ab6be7b8fee47dc82f29a7daf1373178e61ad1`. Inspección **estática** de 150 editoriales, 11 sellos y 55 libros. Los 55 tienen exactamente uno de los dos enlaces editoriales; 18 observaciones de E4 dentro de 13 listas de hosts revisados, pero **4** conciernen a sellos solo bibliográficos y nunca implican recepción de manuscritos. Umbral E5 provisional: **24 fichas** candidatas a reverificación; no supone que estén incorrectas.

**Riesgo nuevo:** el ruleset activo `main-production-integrity` (ID 21661257) mantiene los seis controles CI obligatorios, pero exige **0 aprobaciones humanas** y `require_code_owner_review=false`. Una PR humana no constituye por sí sola una garantía de aprobación. Antes de integrar cambios de `data/editoriales.json` se necesita una **protección efectiva por ruta o revisión autenticada en GitHub**, sin bloquear la automatización editorial legítima del catálogo; todavía no configurada.

**Código:** `scripts/research/gpt_editoriales_approval_contract.py` y `tests/test_gpt_editoriales_approval_contract.py` (20 pruebas adicionales **sin ejecutar**). El código consume el directorio, informes E4/E5 e intención declarada; bloquea modificaciones basándose en huellas SHA-256 canónicas del contenido, fecha, antiguo valor, fuente y propósito explícito por sello. **Nunca escribe** cambios ni acepta `approve` dentro de JSON como autorización auténtica. Solo revisa de momento `status=open/closed`; otros datos necesitan aprobación conjunta, esquema y controles externos. El SHA del commit que aporta el manifiesto **tampoco está autenticado offline**: integración futura debe verificar GitHub `main` exacto.

**Estado:** **77 tests sintéticos escritos en cinco módulos, ninguno ejecutado**. El siguiente «siguiente investigación de GPT» debe continuar **E6.3**, con un piloto offline de cinco registros y revisión de incompatibilidades, sin segundo workflow ni auto-merge. No alterar `main` ni reglas hasta decidir explícitamente cómo garantizar la revisión humana.


## E6.3 — piloto acotado con cinco páginas oficiales (22/10/2026)

Datos y fuentes originales: [editoriales-piloto-5-fuentes-2026-10-22.json](editoriales-piloto-5-fuentes-2026-10-22.json). Comparación con main en commit 72ab6be7b8fee47dc82f29a7daf1373178e61ad1.

| Editorial | Fuente oficial y observación | Estado actual | Acción |
|---|---|---|---|
| [Alienta](https://www.planetadelibros.com/editorial/alienta-editorial/15) | Declara que acepta originales: ensayo/no ficción, archivo digital, máximo uno por autor | Ausente de las 150 | **Candidata nueva**, preparar ficha completa y revisión; no publicar |
| [Anagrama](https://www.anagrama-ed.es/manuscritos) | Declara pausa temporal | closed | Sin cambio |
| [Nocturna](https://www.nocturnaediciones.com/contacto) | Declaración expresa de envío y canal de prensa distinto | open | Sin cambio |
| [Minotauro](https://www.planetadelibros.com/editorial/minotauro/21) | Requisitos expresos y contacto específico | open | Sin cambio |
| [Alfaguara/PRH](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/) | Canal del grupo por sello; no certifica recepción individual | unknown | Mantener unknown |

**Código incremental realizado:** ampliar el módulo existente scripts/research/gpt_editoriales_contact_evidence.py con la función draft_from_html, que recibe HTML como entrada, una URL exacta previamente aprobada, la editorial y la fecha. Produce exclusivamente un candidato y fragmento muy breve, siempre para revisión. Se han añadido pruebas sintéticas al test E4 existente, en vez de abrir un sexto módulo.

**Prueba efectuada:** 13 comprobaciones locales sobre fragmentos sintéticos (positivos, ausencia de evidencia, script no visible, URL fuera de la allowlist y veto de publicación) sin fallos. **No son pruebas con HTML real de las editoriales**, ni la batería de pruebas del repositorio, ni CI: la conexión completa todavía no está validada.

**Soluciones públicas evaluadas:** extruct (BSD-3-Clause) extrae JSON-LD/Microdata pero no las políticas de recepción redactadas como texto; selectolax (MIT) puede ayudar con bloques HTML si el piloto demuestra que el parser estándar pierde contexto. Ninguna dependencia añadida por anticipado. La siguiente pasada debe **alimentar el extractor con el cliente CachedHTTP que ya existe en scripts/reading_editorial_sources.py**, aprovechando sus límites, robots y caché, y comparar las cinco salidas con fuente oficial. Contabilizar solicitudes físicas, incluidas las de robots.txt, fallos, falsos positivos y minutos humanos de revisión. No crear un segundo cron.

**Criterio de utilidad:** un candidato de alta nuevo (Alienta) y cuatro comprobaciones de control, sin importar automáticamente emails ni cambiar estados. Si el HTML real no da fragmentos o hay falsos positivos, corregir solo el extractor antes de ampliar. Cuando se valide, elaborar la propuesta de ficha Alienta con los campos exigidos por build-editoriales.py; no modificar main desde esta PR.

**Estado:** sin HTML real descargado, sin pruebas integradas/Actions y sin publicación. Se mantienen los módulos de E1-E6 como material de investigación, no como arquitectura aprobada.


### Comprobación puntual de fuentes y fallo corregido (22/10/2026)

- **Fuentes actuales consultadas:** [Anagrama, manuscritos](https://www.anagrama-ed.es/manuscritos) confirma recepción pausada; [Nocturna, contacto](https://www.nocturnaediciones.com/contacto) confirma el canal de originales; [Minotauro, sello](https://www.planetadelibros.com/editorial/minotauro/21) confirma condiciones de proyectos; [Alienta, sello](https://www.planetadelibros.com/editorial/alienta-editorial/15) confirma recepción de ensayos inéditos; [Penguin, envío](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/) solo acredita procedimiento corporativo, **no** el estado particular de Alfaguara.
- **5 anclas breves reales del texto publicado**, añadidas al test `test_gpt_editoriales_contact_evidence.py`. Una comprobación local de las cinco reglas de extracción sobre fragmentos HTML reconstruidos con esas anclas obtuvo **5/5 decisiones esperadas**. **No prueba HTML bruto completo, selectores, red ni el test de la rama entera**.
- **Defecto localizado y corregido:** `draft_from_html()` usaba índices obtenidos del texto normalizado sin tildes para recortar texto original Unicode; con muchas tildes podía recortar otro fragmento. Ahora devuelve la **coincidencia normalizada** y suprime cualquier dirección de correo que pudiera aparecer dentro de ese fragmento. Se incorporó un test de que las cinco anclas no exponen `@`.
- **Alienta, comprobación estática contra builder real** `scripts/build-editoriales.py`: el borrador tiene los **18 campos obligatorios**, slug que no colisiona con las 150 entradas de `main`, fuente primaria HTTPS, historial y longitudes mínimas; no se detectó incompatibilidad en los requisitos inspeccionados. `publish=false` es **intencionado** para no generar una ficha pública. **No se ha ejecutado el builder** con ese fichero ni se han comprobado efectos de renderizado.
- **Próxima validación indispensable:** ejecutar con HTML completo aprobado el modo optativo `--live-pilot` y el test Python de la rama; observar bloqueos de robots, contadores y extracción antes de cambiar estados o activar la ficha Alienta. No escalar a más editoriales por ahora.

### E6.3 — puente al cliente HTTP existente (continuación)

**Código actualizado sin crear un sexto módulo:** la función run_live_pilot() y la opción --live-pilot del módulo E4 existente scripts/research/gpt_editoriales_contact_evidence.py. Importa CachedHTTP de scripts/reading_editorial_sources.py (ya integrado en main) y reutiliza sus controles de robots.txt, hosts, redirecciones, caché y presupuesto. Verifica, además, las **cinco URLs exactas** independientemente de los datos del informe; Alienta está añadida a la whitelist de hosts oficial del piloto.

**Salida del prototipo:** JSON con estado propuesto o desconocido, éxito/error de acceso, URL, fecha, cinco decisiones pendientes, contador de solicitudes físicas (incluidas comprobaciones robots y redirecciones), aciertos de caché y veto permanente de publicación. No copia direcciones de correo ni modifica data/editoriales.json. El reporte opcional solo se admite bajo .ci/reading-intake/, carpeta que ya utiliza el workflow para subir informes de ingesta.

**Reproducción propuesta desde la raíz del repositorio, con acceso autorizado y sin automatización programada. No ejecutado:**

    python scripts/research/gpt_editoriales_contact_evidence.py \
      --live-pilot \
      --pilot-cases docs/research/gpt/editoriales-piloto-5-fuentes-2026-10-22.json \
      --trusted-hosts docs/research/gpt/editoriales-e4-trusted-hosts-2026-10-22.json \
      --as-of 2026-10-22 \
      --cache-dir .ci/reading-editorial-cache \
      --budget 12 \
      --output .ci/reading-intake/editorial-candidates-pilot.json

**Pruebas sin red añadidas** al test E4 existente: FakeHTTP con cinco respuestas, fallo de una fuente sin invalidar las otras, URL diferente dentro de un dominio aprobado y selección incompleta. Comando para comprobar el código:

    python -m unittest discover -s tests -p 'test_gpt_editoriales_contact_evidence.py' -v

**Límite verificado:** el HTML completo no ha podido descargarse desde el contenedor por falta de acceso de red. El navegador de consulta devuelve texto renderizado, no bytes HTML ni cabeceras. Tampoco se pudo consultar robots.txt por navegador, así que CachedHTTP debe comprobarlo antes de cada acceso en el entorno ejecutor. **No se ha ejecutado el modo live ni la batería unittest del repositorio**; ningún éxito sintético anterior demuestra que las expresiones funcionen con todo el DOM real. Tampoco se ha activado CI, ninguna PR de publicación ni nuevo cron.

**Próxima iteración útil:** ejecutar el comando en entorno autorizado, revisar cinco resultados y sus solicitudes reales, y corregir únicamente las expresiones/páginas que fallen. Después validar con el builder existente la ficha de Alienta y preparar la aprobación de un cambio de datos, sin añadir bibliotecas externas por anticipado.


### Siguiente avance — validación real de Alienta con el builder existente

Se ha incorporado **un test concreto, sin introducir otro módulo**, en `tests/test_gpt_editoriales_contact_evidence.py`: `AlientaRealBuilderContractTests.test_alienta_passes_builder_but_is_not_published`. El test carga el directorio vigente de `data/editoriales.json` y la propuesta de Alienta de esta PR, forma un JSON temporal, y llama al **mismo** `scripts/build-editoriales.py` que construye la web.

Comprueba en dos etapas: (1) `publish=false` no altera el recuento ni crea páginas; (2) con `publish=true` **solo dentro del archivo temporal**, el constructor en `check_only=True` admitiría una ficha adicional sin escribir en el repositorio. También comprueba que no hay colisión de slug y que la propuesta tiene fuente primaria. De ese modo, **Cloud no necesita traducir a mano la ficha de investigación**: basta ejecutar el test contra el `main` correspondiente y corregir los fallos que arroje.

**Comprobación parcial ejecutada el 22/10/2026:** se obtuvo la función de producción `validate_record()` de `scripts/build-editoriales.py` en el `main` actualizado (blob `401a975af62905cbf2f5cce49a654d09781a39fc`) y se ejecutó localmente, con sus funciones auxiliares copiadas, sobre los **21 campos de la candidata Alienta**: (1) `publish=false` **válido**, con el único aviso de no publicación; (2) `publish=true` **válido** solo en memoria, sin avisos; (3) estado `closed` con correo de manuscritos, (4) slug duplicado y (5) fecha futura, **los tres rechazados**. Resultado **5/5 conforme a las expectativas**. Se contrastó además en el directorio vigente de `main` que no existe el slug `alienta-editorial`. La fuente oficial [PlanetadeLibros](https://www.planetadelibros.com/editorial/alienta-editorial/15) mantiene expresamente la recepción de ensayos inéditos. **Límite:** esta ejecución utiliza la función exacta del validador en un entorno aislado, no la totalidad del programa con los 150 registros ni el renderizador. El nuevo test que invoca `builder.build(check_only=True)` en el checkout completo sigue sin ejecutarse y ninguna página fue publicada. Para completarlo en un checkout con acceso:

    python -m unittest discover -s tests -p 'test_gpt_editoriales_contact_evidence.py' -v

Si el test pasa, el siguiente paso sería obtener los cinco HTML originales con `--live-pilot` mediante `CachedHTTP` y comparar las salidas. Los dos requisitos son complementarios: **datos válidos en builder** y **detección correcta en la fuente**. No añadir fichas a `main` hasta comprobar ambos.



### Corrección verificada en lógica aislada: contradicciones de recepción

El piloto E6.3 tenía un falso positivo reproducible: la búsqueda de «enviar por correo electrónico» devolvía `open` incluso si, a continuación, la misma frase indicaba que la recepción estaba cerrada. Se añadieron dos casos negativos y se cambió **solo** el extractor E4 existente: ante `no aceptamos manuscritos`, `recepción de originales cerrada/pausada/suspendida` o `no lo haga por correo electrónico` en la proximidad de una coincidencia `open`, el resultado es `unknown`, con motivo «contradicción, revisión humana». No deduce automáticamente `closed`.

**Control de regresión:** la regla no debe bloquear una editorial que sí acepta originales digitales pero **no físicos**, ni a Alienta por no publicar **ficción**. Dos casos de control positivo también añadidos al fichero `tests/test_gpt_editoriales_contact_evidence.py`.

**Ejecución local verificable con una copia aislada del extractor**, no el checkout integral del repositorio: 13 comprobaciones sintéticas de base, 5 anclas cortas de páginas oficiales reconstruidas en HTML y 4 comprobaciones nuevas (2 contradicciones, 2 restricciones legítimas) completadas sin errores. **No** significa que las pruebas completas de la PR ni el HTML bruto de las cinco webs hayan pasado. La regla de proximidad es conservadora y provisional: en una página larga podría necesitar segmentación de secciones tras la prueba con HTML real. En esta pasada no se añadieron librerías ni un módulo nuevo.



### E6.3 — dato nuevo aprovechable: buzón específico para originales

**Código incremental aplicado sobre el módulo E4 existente:** función submission_email_candidate() y campos submission_email_candidate y submission_email_basis en el resultado de draft_from_html(). Analiza el texto oficial ya obtenido por CachedHTTP y solo propone un buzón si sigue una instrucción explícita de envío de manuscritos en una de estas tres páginas revisadas: Nocturna, Minotauro o Alienta. Además verifica el dominio del correo. Las demás fuentes, incluidas Anagrama (pausa) y Alfaguara (procedimiento de grupo), no proponen direcciones. Un correo de prensa, lector o premio nunca se sustituye por un correo de envío de originales. **Siempre publish=false y revisión humana: no se actualiza data/editoriales.json ni se envía correo.**

**Resultados comparables con el código del sitio, 22/10/2026:**
- **Nocturna**: el buzón específico de originales de [su página oficial](https://www.nocturnaediciones.com/contacto) **coincide** con submission_email de main.
- **Minotauro**: el buzón para enviar proyectos de [su web oficial](https://www.planetadelibros.com/editorial/minotauro/21) **coincide** con submission_email de main; es distinto del correo de lectores, premios y prensa publicado en la misma página.
- **Alienta**: el buzón para originales digitales de [su web oficial](https://www.planetadelibros.com/editorial/alienta-editorial/15) **coincide** con el borrador de alta de #692; todavía NO está en el directorio de main.

**Prueba local de la función aislada:** 11 comprobaciones (3 coincidencias correctas, 8 exclusiones o casos negativos), sin fallos. Añadidos cinco métodos de prueba al archivo E4 existente. Se usaron fragmentos representativos basados en el texto visible de fuentes oficiales. **No es una ejecución del HTML completo vía CachedHTTP ni de toda la suite GitHub**. El informe de candidatos solo se genera en el modo optativo de investigación, no se publica.

**Ganancia funcional:** pasamos de detectar un posible estado de recepción a identificar el dato de envío adecuado con procedencia y contraste; dos contactos ya publicados se verificaron contra main y Alienta constituye una candidata a ficha adicional. El próximo paso no es aumentar controles: ejecutar las cinco URL con el cliente actual, cuantificar diferencias y corregir los errores observados antes de publicar nada.


### Última corrección incremental — cierre frente a restricciones y métricas verificables

**Defecto reproducido en el extractor aislado:** cuando una página contenía la instrucción de envío y después «No recibimos originales actualmente» o «Ya no estamos aceptando manuscritos», el piloto todavía proponía **open**. El patrón anterior tampoco distinguía correctamente una restricción «No aceptamos manuscritos de ficción». Se amplió *únicamente* la expresión de negación del extractor E4, eliminando la coincidencia demasiado amplia. **Resultado de control local:** los cuatro casos de cierre ahora producen **unknown**; tres restricciones de formato/género conservan **open**. Los 13 controles sintéticos anteriores, las cinco anclas oficiales reconstruidas, 11 aserciones de buzones y cinco casos end-to-end reconstruidos siguieron pasando en la copia local de la lógica; **no son pruebas del checkout completo ni HTML oficial original**.

**Métrica pequeña incorporada al modo --live-pilot existente:** cada salida incluye la propuesta previa revisada manualmente, si se facilitó, y si coincide con lo extraído. El informe separa:
- compared_to_prior_review: páginas obtenidas y con un estado de referencia;
- matched_prior_review: coincidencias con esa referencia;
- differences_needing_human_review: contradicciones que requieren inspección;
- retrieval_failures: páginas no accesibles, **sin clasificarlas como contradicción**.

Se añadieron dos tests offline mediante FakeHTTP al test E4 existente. **Pendiente ejecutarlos en el checkout completo.** Estas métricas no equivalen a precisión estadística ni autorizan actualizaciones: solo hacen visible lo que cambió respecto a las cinco comprobaciones manuales previas.

**Punto siguiente:** ejecutar los tests Python con el repositorio completo y un piloto de las cinco URLs, usando el cliente CachedHTTP existente; registrar peticiones, bloqueos, discrepancias y resultado del builder de Alienta. Si un caso falla, corregir su regla o fuente concretas antes de ampliar a otras editoriales. Sin cron nuevo, sin publicar el directorio.

### Piloto E6.3 — procedencia de respuesta y caché

**Problema concreto en el piloto:** `draft_from_html` asigna al resultado la fecha de procesamiento. Sin más datos, una respuesta reutilizada de caché (hasta 24 horas en el cliente existente) podría interpretarse como una descarga realizada ese mismo día. El código de `CachedHTTP` en `main` **ya escribe** un JSON junto al cuerpo con la marca `retrieved_at`, por lo que no hace falta otro sistema de consultas.

**Solución aplicada solo al modo `run_live_pilot` existente:** cada fuente incorpora `content_sha256`, `content_bytes`, `served_from_cache` y `source_retrieved_at_unix` cuando la marca del cliente está disponible. Si falla la descarga, esas medidas son `null`, no pruebas inventadas. La fecha de procesamiento y la de obtención se distinguen. El SHA-256 permite comparar dos observaciones y saber si el HTML recibido realmente cambió, aunque el estado extraído permanezca igual.

**Pruebas añadidas al archivo existente** `tests/test_gpt_editoriales_contact_evidence.py`: un FakeHTTP comprueba la huella del contenido; otro simula cinco aciertos de caché y comprueba que el informe no los clasifica como nuevas descargas. Estas dos pruebas están **escritas pero todavía NO ejecutadas contra el checkout completo**. Se mantiene la prohibición de escribir en `data/editoriales.json`.

**Siguiente comprobación que aporta valor:** ejecutar el piloto sobre los cinco sitios oficiales con el repositorio completo; examinar discrepancias, número de solicitudes, errores y si una respuesta es nueva o cacheada. Los cambios de contenido sin cambio de estado pueden señalar que conviene revisar requisitos de envío. Si los cinco casos son estables, entonces probar la alta no publicable de Alienta con el builder real; no ampliar editoriales ni añadir librerías por inercia.

### Corrección E6.3 — métricas de caché verificables

**Bug real detectado leyendo código en `main`:** `CachedHTTP.hits` incrementa tanto con la caché de la página como con la de `robots.txt`. La primera implementación del piloto equiparaba `hits_after > hits_before` con «esta página procede de caché», lo cual era incorrecto. **Solución puntual** en `run_live_pilot()`: comprobar la entrada `<sha256(url)>.body/.json` de **esa URL** antes de solicitarla, usando las mismas condiciones de edad (24 horas) y tamaño (2 MB) que `CachedHTTP`. El informe también registra `content_sha256`, `content_bytes` y `source_retrieved_at_unix` desde la marca de recuperación que ya escribe el cliente. Un fallo de acceso deja estas mediciones a `null`; **no se infiere que la fuente se consultó hoy si solo estaba cacheada**.

**Prueba sustantiva preparada, no ejecutada:** `test_replays_five_pages_offline_with_real_cached_http` en `tests/test_gpt_editoriales_contact_evidence.py` utiliza **la clase real** de `scripts/reading_editorial_sources.py` con cinco HTML y los cuatro `robots.txt` almacenados en un directorio temporal. Debe obtener las cinco decisiones correctas, con cero llamadas físicas y la fecha original del caché conservada. Otro test reproduce el fallo antiguo: un acierto de `robots.txt` sin caché de la página **no** debe activar `served_from_cache`. Se corrigieron los tests FakeHTTP anteriores para que, si el cliente falso no expone su entrada de caché, el valor sea `null` y no se invente su procedencia.

**Verificación realmente ejecutada aquí:** los cuatro scripts aislados ya existentes en `/mnt/data/gpt-pilot` terminan correctamente (13 comprobaciones sintéticas de reglas, 5 anclas de páginas, 11 aserciones de buzones y 5 casos de extremo a extremo **sobre HTML reconstruido**). No equivalen a ejecutar el código completo de GitHub. El contenedor no resuelve el dominio GitHub para un checkout completo y tampoco puede recuperar el HTML original de esas webs, por lo que **la nueva prueba de integración con la clase real queda preparada, sin resultado ejecutado**. No se ha llamado a Actions ni modificado `main`.

**Siguiente comprobación, solo una:** desde checkout del proyecto con acceso a las fuentes, ejecutar `python -m unittest discover -s tests -p 'test_gpt_editoriales_contact_evidence.py' -v`; inspeccionar la prueba con caché real y, si pasa, correr el comando `--live-pilot` ya documentado contra las cinco URLs y comparar huella, fecha real, recibidos/bloqueados y correspondencia con la revisión humana. Si falla, corregir únicamente lo observado.

### E6.3 — puente de salida del piloto hacia E4 (22/10/2026)

**Problema real:** el modo optativo de cinco páginas generaba estados y correos candidatos en su propio JSON, pero no observaciones con el contrato ya establecido de E4. Integrarlo obligaba a traducir esos resultados manualmente o crear otra capa.

**Cambio localizado en el mismo módulo:** `run_live_pilot()` incorpora `pending_review_observations` (`schema_version=1` y `observations` con ID, slug, propósito, alcance, fuente, fecha y fragmento breve sin direcciones). Conexiones: `open → submissions_open`, `paused → submissions_paused`, `group_only → group_submission_channel`; páginas fallidas o `unknown` no generan evidencia. Cada entrada lleva `origin=html_pilot_unreviewed`.

**Puerta expresa:** `review()`, función E4 que ya existía, rechaza esta procedencia como `automated_evidence_needs_human_review`, incluso si la URL pertenece a un host aprobado. Cloud puede leer los cinco borradores, revisar el contenido oficial y redactar las observaciones humanas por separado; **el JSON de una extracción NO demuestra que alguien lo aprobó**, ni permite publicar. Sigue intacto el veto de datos públicos y de auto-merge.

**Pruebas añadidas en el test E4 existente**, sin nuevas bibliotecas: cinco HTML sintéticos → cinco observaciones en esquema E4 → las cinco rechazadas por `review()`; cinco páginas sin declaración (una inaccesible) → cero observaciones y fallo de acceso separado. **Esas dos pruebas aún no se han ejecutado contra el checkout completo**. Se han mantenido los antiguos casos sintéticos disponibles, que siguen pasando con la copia local anterior del extractor, pero no deben presentarse como validación de estos cambios recientes.

**Siguiente comprobación única:** ejecutar `tests/test_gpt_editoriales_contact_evidence.py` en el checkout actual. Si falla el contrato entre las funciones E4, corregirlo antes de integrar otra fuente o añadir un nuevo módulo. Fuentes públicas comprobadas en [Anagrama](https://www.anagrama-ed.es/manuscritos), [Nocturna](https://www.nocturnaediciones.com/contacto), [Alienta](https://www.planetadelibros.com/editorial/alienta-editorial/15), [Minotauro](https://www.planetadelibros.com/editorial/minotauro/21) y [Penguin](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/).


### E6.3 — falso positivo desde HTML inerte, corregido (22/10/2026)

**Fallo reproducido antes del cambio:** el extractor devolvía `open` cuando la única frase «Alienta Editorial acepta la recepción de manuscritos originales» aparecía dentro de `<template>` o `<head><title>…</title></head>`, aunque el cuerpo solo mostrase contacto general. La documentación del elemento `template` en [MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/template) confirma que su contenido no se muestra por defecto. **No se trata de una anomalía observada en una editorial concreta**, sino de dos casos HTML controlados que revelan un falso positivo del parser existente.

**Corrección mínima:** `_PilotVisibleText` ahora ignora `head`, `title` y `template`, además de los elementos `script/style/noscript/svg` que ya ignoraba. Para una plantilla que se renderiza dinámicamente, el resultado conservador será `unknown` hasta poder inspeccionar el DOM visible; no se inventa recepción. Se han añadido dos métodos de regresión al test E4 **existente**.

**Comprobación local realizada sobre la copia aislada del extractor:** los dos casos que antes daban `open` ahora producen `unknown`; las frases efectivamente presentes en el cuerpo siguen dando `open` (dos controles). Los cuatro scripts locales anteriores (13 casos sintéticos, cinco anclas, cinco casos de extracción reconstruidos y 11 comprobaciones de buzones) continúan terminando correctamente. **La copia local no equivale a ejecutar la suite de la rama de GitHub ni garantiza que el HTML completo de las cinco webs se analice bien.**

**Siguiente paso único, sin más arquitectura:** ejecutar el test E4 del checkout completo y después el modo `--live-pilot` de cinco URLs. Si aparecen diferencias en DOM, corregir esos casos concretos. Ningún cambio en `main`.


### Corrección E6.3 — bloques ocultos y texto no fiable (22/10/2026)

**Fallo real de código reproducido localmente, no observado como incidente en una editorial:** la frase de recepción de Alienta colocada **únicamente** dentro de un bloque HTML con atributo `hidden`, `aria-hidden="true"` o estilo inline `display:none` devolvía `open` (tres falsos positivos). Se identificó directamente en el parser `_PilotVisibleText`: ignoraba `head` y `template`, pero no los atributos de sus contenedores. Las referencias públicas actuales son [MDN: `hidden`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/hidden) y [MDN: `aria-hidden`](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-hidden).

**Corrección aplicada sin dependencia nueva:** seguimiento mínimo de etiquetas anidadas y profundidad de bloques excluidos; descarta `hidden`, `display:none` y `visibility:hidden` inline, además de `aria-hidden=true`, y mantiene el contenido situado después de un bloque descartado. Evita que `br`, `img` u otras etiquetas HTML vacías alteren la pila. Con `aria-hidden=true` **no afirmamos que el contenido sea visualmente invisible** (MDN confirma que solo lo oculta del árbol de accesibilidad): preferimos `unknown` si el único respaldo se encuentra en una región excluida de la representación accesible. Una hoja CSS externa o el DOM dinámico pueden modificar visibilidad y siguen fuera de este parser; por ello no se considera una implementación de navegador.

**Pruebas ejecutadas localmente sobre la implementación aislada del extractor:** los tres errores iniciales ya producen `unknown`. Otras cinco comprobaciones —`visibility:hidden`, texto visible posterior, presencia de `img`/`br`, bloque visible y `template`— alcanzan los resultados esperados: **8/8 regresiones**. También se ejecutaron los cuatro scripts existentes de 13+5+5+11 comprobaciones: todos completaron sin fallos. **No se ejecutó la suite GitHub completa, ni se procesó HTML íntegro oficial.** Se añadieron dos métodos al archivo de tests E4 existente en #692 para que ese fallo no reaparezca.

**Siguiente acción útil:** en un checkout del repositorio, ejecutar el test E4 completo (incluida la prueba de `CachedHTTP` real precargado), corregir cualquier incompatibilidad efectiva y después comparar las cinco URLs oficiales mediante `--live-pilot`. No ampliar los patrones ni las dependencias hasta observar un fallo en esas fuentes.
