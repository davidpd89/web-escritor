# Investigación de GPT — editoriales, sellos y contactos

**P0 · DRAFT · NO MERGEAR.** Coordinación: [#691](https://github.com/davidpd89/web-escritor/pull/691). Dependencias: catálogo [#687](https://github.com/davidpd89/web-escritor/pull/687), investigación de proveedores [#680](https://github.com/davidpd89/web-escritor/pull/680), auditoría de sellos [#683](https://github.com/davidpd89/web-escritor/pull/683).

## Gap exacto (revisado 22/10/2026)

En `main`, `data/editoriales.json` contiene **150** editoriales con fuentes, web y estado de recepción (72 open, 45 closed, 26 unknown, 7 indirect); solo **54** incluyen un correo específico de manuscritos. El constructor `scripts/build-editoriales.py` genera fichas y alerta de verificaciones antiguas. No hay captación universal automática ni actualización fiable continua de estado/contactos.

La **PR #687 aún abierta** introduce `data/reading-publishers.json`: **11 sellos** descubiertos por libros de Penguin, con URL bibliográfica y ficha de sello. Son **identidades bibliográficas**, no pruebas de que reciban manuscritos. No deben fusionarse semánticamente con el directorio de recepción sin resolver aliases, grupos y contactos.

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
- **E2:** probar vía oficial ISBN y licencias; elegir fuente inicial y límites; guardar respuesta representativa autorizada como fixture anonimizado/sintético.
- **E3 CÓDIGO PREPARADO:** `scripts/research/gpt_editoriales_reconcile.py` ya compara, en modo solo lectura y con ficheros suministrados explícitamente, slugs, alias sugeridos, datos obsoletos, fuentes de ficha, registros sin libros y enlaces rotos. Devuelve JSON para revisión sin filtrar correos ni escribir `data/editoriales.json`. **No probado todavía**; #692 no contiene los 11 sellos porque viven en #687. Se utilizará una copia local de esos datos después de aprobación.
- **E4 EN PREPARACIÓN:** `tests/test_gpt_editoriales_reconcile.py` añade 11 pruebas sintéticas escritas **sin ejecutar** (estado cerrado que sigue publicando, alias, homónimos/colisiones, fuente impostora, libro sin enlace y caducidad). Pendiente contrastar los primeros 20 candidatos reales, criterios de correspondencia jurídica y contactos oficiales.
- **E5:** piloto incremental con presupuesto y reporte; integración futura al único publicador, después de QA y revisión legal, sin segundo workflow.

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

El conciliador necesita **tres ficheros explícitos**; `main` todavía no contiene `reading-publishers.json`. Tras disponer de una copia de la #687 para investigación:

```sh
python scripts/research/gpt_editoriales_reconcile.py \
  --directory data/editoriales.json \
  --catalogue-publishers /ruta/revisada/reading-publishers.json \
  --books /ruta/revisada/reading-catalogue.json \
  --as-of 2026-10-22
```

Salida: JSON en stdout con recuentos, colisiones, casos huérfanos y `imprint_candidates` con `decision=review_*|catalogue_only|quarantine_source`. Solo sugerencias, **jamás fusiones, cambios de status o alta directa**. Los datos deben provenir del **mismo commit** de #687 para evitar falsos errores referenciales. La rama no añade ni altera jobs, workflows ni datos públicos.

**Siguiente acción recomendada — E2/E4:** obtener permiso o export de la base ISBN; luego preparar 20 coincidencias reales manualmente y probar la validez/atribución de contacto antes de automatizar una sola ficha. Se mantiene el coste objetivo cero.
