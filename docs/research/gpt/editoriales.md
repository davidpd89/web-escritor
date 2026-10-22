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

- **E1 (ahora):** auditar claves/duplicados y enlaces reales entre los 150 registros y los 11 sellos propuestos en #687; registrar colisiones y un caso verificable de editorial `closed` que sigue publicando.
- **E2:** probar vía oficial ISBN y licencias; elegir fuente inicial y límites; guardar respuesta representativa autorizada como fixture anonimizado/sintético.
- **E3:** código offline `scripts/research/gpt_editoriales_reconcile.py` (propuesta, **todavía inexistente**) para comparar registros y emitir JSON de candidatos, sin escribir `data/editoriales.json`.
- **E4:** contrato de fuente/estatus, tests sin red con alias, grupos, sello vs empresa, URL dudosa, cambios de estado, campos obsoletos; revisión manual de primeras 20 entidades.
- **E5:** piloto incremental con presupuesto y reporte; integración futura al único publicador, después de QA y revisión legal, sin segundo workflow.

**Criterio de salida:** demo offline reproducible, cero duplicados publicados, contactos con procedencia, ninguno de los 150 estados alterado sin verificación y coste de servicios externos 0 €. Si no se permite usar una fuente, se documenta NO-GO y alternativa.

**No ejecutado:** ninguna prueba, extracción masiva, edición de datos públicos o publicación.
