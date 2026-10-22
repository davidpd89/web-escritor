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

**E4 terminada**: [informe específico](editoriales-e4-resultados-2026-10-22.md). **E5 terminada como investigación y propuesta no ejecutada**: [diseño de integración E5](editoriales-e5-integracion-2026-10-22.md). #687 se ha **fusionado**; ya no es dependencia abierta. **Próxima petición «siguiente investigación de GPT» → E6.1 y E6.2**, en la misma PR #692: comprobar esquemas cruzados de los cuatro módulos con los nuevos datos de `main`, y redactar el contrato de aprobación humana por campo. No ejecutar CI ni publicar automáticamente.


**Actualización de estado 22/10/2026:** #687 fusionada en `main` durante E5. `main` contiene 55 libros (35 enlazan al directorio, 20 a sellos exclusivos), 55 autores, 11 sellos y 150 editoriales. Los informes E1/E4 conservan su procedencia histórica de la rama #687; E6 debe usar **únicamente los datos de `main` del mismo commit**. #692 sigue DRAFT y sin tests ejecutados.
