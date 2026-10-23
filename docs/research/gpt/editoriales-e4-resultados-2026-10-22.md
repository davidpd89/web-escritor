> Archivo de investigación anterior a la reducción de alcance de #692. Las afirmaciones de pruebas pendientes y las referencias a módulos retirados son históricas. Véase [estado comprobado y uso actual](editoriales.md).

# E4 · Fuentes reales, identidad y contactos (22/10/2026)

**PR #692 · DRAFT / investigación.** Las observaciones de abajo **no** implican cambios en producción. Fuentes consultadas directamente; no se han visitado por crawler propio ni importado listados ajenos.

## 1. Muestra cerrada y comprobable

- [15 entidades auditadas, con fuente, estado del QID y advertencias](editoriales-muestra-e4-2026-10-22.json): 13 editoriales/sellos + 2 grupos. **6/15** con un QID localizado y revisado en Wikidata, **9/15** sin QID acreditado en esta pasada. De los seis, **cinco** son candidatos de entidad y **uno** (Bruguera Q3275000) requiere relación histórica, no equivalencia con el sello activo.
- En esos **seis QIDs**: **P856** (web oficial) aparece en cuatro; **tres** URLs son HTTP y **una** HTTPS; dos no lo contienen. El adaptador de investigación acepta HTTPS y no inventa una redirección de HTTP a HTTPS. Si falta P856, el sitio oficial se verifica directamente en la editorial. **No extrapolar estos porcentajes a Wikidata en conjunto**.
- Relaciones corporativas: **P749** (organización matriz) y **P127** (propietario) son distintas; se han guardado por separado. Ejemplos: [Editorial Planeta Q2339634](https://www.wikidata.org/wiki/Q2339634) incluye matriz Grupo Planeta; [Anagrama Q8772125](https://www.wikidata.org/wiki/Q8772125) y [Alfaguara Q3324371](https://www.wikidata.org/wiki/Q3324371) tienen propiedad declarada (P127). Esto **no** significa que un grupo reciba manuscritos en nombre de todas sus marcas.
- **Caso de alto riesgo:** [Bruguera Q3275000](https://www.wikidata.org/wiki/Q3275000) describe una empresa disuelta en 1986; [Penguin publica actualmente el sello Bruguera](https://www.penguinrandomhousegrupoeditorial.com/sello/bruguera/). Hay continuidad de marca/fondo, **no identidad jurídica automáticamente demostrada**. Mantener IDs distintos hasta documentar el vínculo histórico.
- **Dos entradas del catálogo de #687 sin libro asociado**: Beascoa y Montena; [ambos aparecen como sellos activos](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/nuestros-sellos/). «Sin libros en nuestro catálogo» **no significa** «sello inactivo».

## 2. Evidencia primaria de contactos: 18 observaciones

Se han preparado [18 observaciones de finalidad explícita](editoriales-e4-observaciones-2026-10-22.json) y una [lista independiente de dominios oficiales](editoriales-e4-trusted-hosts-2026-10-22.json) para 13 sellos. Las observaciones son **resúmenes propios** con URL y fecha, sin correos personales ni corporativos copiados. Casos representativos:

| Entidad | Fuente primaria | Hecho puntual observado | Qué propondría el motor |
|---|---|---|---|
| **Minotauro** | [Página oficial](https://www.planetadelibros.com/editorial/minotauro/21) | Proyectos, información para lectores y prensa usan vías **distintas** | `open` a **revisar** por fuente específica; canales clasificados |
| **Nocturna** | [Contacto](https://www.nocturnaediciones.com/contacto) | Admite novelas por una vía concreta y separa prensa | `open` a **revisar**, sin incorporar correos |
| **Anagrama** | [Manuscritos](https://www.anagrama-ed.es/manuscritos) + [contacto](https://www.anagrama-ed.es/contacto) | Recepción **pausada** mientras mantiene atención general y prensa | `closed` a **revisar**, canales generales intactos |
| **Alfaguara, Grijalbo, Salamandra y Plaza & Janés** | [PRHGE, envíos](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/) | El grupo describe formulario y selección de sello | `not_inferred`, **nunca** heredar `open` sin prueba individual |
| **Editorial Planeta** | [Ficha del sello](https://www.planetadelibros.com/editorial/editorial-planeta/8) | Publica contacto editorial | `general_contact` no equivale a admisión de originales |
| **Tusquets** | [Ficha oficial](https://www.planetadelibros.com/editorial/tusquets-editores/59) | Publica contacto general | No inferir recepción |
| **Bruguera / Debate / Montena / Beascoa** | [PRHGE](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/nuestros-sellos/) y fichas Penguin | Hay actividad de sello; no es prueba de recepción | Solo `publisher_imprint` |

**Revisión:** los estados de Nocturna/Minotauro/Anagrama ya figuraban en el directorio anterior; el piloto **no los sobrescribe**. En las editoriales restantes, la política corporativa no rellena automáticamente estados `unknown`.

## 3. Código nuevo preparado, sin ejecución

- `scripts/research/gpt_editoriales_contact_evidence.py`: toma **observaciones manuales** y una **allowlist separada** de hosts aprobados. Clasifica `general_contact`, `press_contact`, `submissions_open`, `submissions_paused`, `group_submission_channel`, `publisher_imprint`. Caducidad provisional: 45 días para estado de recepción y 180 para contacto; tras caducar no transforma `open` en `closed` ni viceversa. Aísla conflictos, fuentes no aprobadas, fechas futuras e intentos de introducir direcciones en notas. Produce propuestas JSON **sin emails, con revisión obligatoria y `publication_allowed=false`**.
- `tests/test_gpt_editoriales_contact_evidence.py`: **15 pruebas sintéticas escritas, ninguna ejecutada** (colisión de estados, fuente ajena, propósito de contacto, caducidad, no heredar grupo, etc.).
- Se amplió `scripts/research/gpt_editoriales_wikidata_candidates.py` para devolver `owner_qids` (P127) **separados** de `parent_qids` (P749), más **una prueba pendiente de ejecutar**. Seguimos sin HTTP, descargas masivas, merge de entidades ni cambios en datos públicos.

Para ejecutar **algún día, solo tras autorización**, el prototipo E4 requiere los dos JSON de esta carpeta:
```sh
python scripts/research/gpt_editoriales_contact_evidence.py \
  --observations docs/research/gpt/editoriales-e4-observaciones-2026-10-22.json \
  --trusted-hosts docs/research/gpt/editoriales-e4-trusted-hosts-2026-10-22.json \
  --as-of 2026-10-22
```
No se ha ejecutado ni conectado a ninguna tarea.

## 4. Código externo útil examinado (no copiado ni instalado)

- [scrapinghub/extruct](https://github.com/scrapinghub/extruct) — **BSD-3-Clause** (LICENSE verificada): interpreta JSON-LD, Microdata y otros metadatos incrustados. Solo ayuda a estructurar fuentes; **no certifica** que un email sea para manuscritos.
- [rushter/selectolax](https://github.com/rushter/selectolax) — **MIT**: parser HTML rápido; candidato si el prototipo stdlib se queda corto en páginas oficiales. No justifica por sí mismo extraer datos masivamente.
- [adbar/trafilatura](https://github.com/adbar/trafilatura) — **Apache-2.0**: extracción de texto web; posible pérdida del **contexto** que distingue contacto general de manuscritos. No es apropiado para decidir `open/closed` sin revisión.
- **Decisión:** en este paso, **ninguna dependencia adicional**. Primero verificar reglas por campo con fuentes oficiales y sin automatización de estados. La reutilización futura debe incluir copyright/licencia y registro de procedencia de cada fragmento copiado.

## 5. Siguiente investigación E5 (en esta misma PR)

1. Hacer reconciliación a partir del `main` vigente y #687 (si ya se fusionó), manteniendo 150 registros y 11 sellos o cifras que correspondan al nuevo commit.
2. Revisar **casos reales conflictivos**, especialmente estado `unknown` frente a un formulario del grupo; confirmar **por sello** si el canal realmente lo acepta; revisar el histórico Bruguera y relaciones matriz/propiedad.
3. Preparar propuesta del **único pipeline incremental** (semillas → candidato → evidencia → revisión → PR de artefactos con checks); presupuesto y política de retirada ante cambios. Sin crawlers paralelos, sin tocar `main`, sin nuevos crons, sin importar contactos de la base ISBN carente de permiso.
4. Pasar las pruebas/offline QA solo cuando se autorice explícitamente esa fase; corregir los problemas que detecten antes de integración. **Esta PR continúa siendo DRAFT y no debe mergearse ahora.**
