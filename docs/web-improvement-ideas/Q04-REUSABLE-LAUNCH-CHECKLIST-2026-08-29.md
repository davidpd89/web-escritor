# Q.4 · Checklist reutilizable de lanzamiento editorial — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `ALREADY_COVERED`.

## 1. Hipótesis original

Q.4 proponía convertir el trabajo del lanzamiento de *Las manecillas del recuerdo* en una checklist editorial reutilizable para futuras obras. El banco original citaba como ejemplos:

- JSON-LD;
- sitemap;
- redirects;
- newsletter;
- prensa;
- y, por extensión, todas las capas técnicas/operativas necesarias para lanzar una obra sin repetir errores.

La hipótesis era correcta, pero la investigación descubrió que el proyecto ya había acumulado runbooks, launch-state, release-readiness y contratos suficientes. Crear otra checklist en pleno lanzamiento habría introducido una segunda autoridad antes de disponer del resultado real de Manecillas.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Estado: `ALREADY_COVERED`.

Conclusión:

- ya existen launch gates/runbooks;
- no duplicar una checklist ahora;
- después del 03/09, usar la evidencia real de Manecillas para convertir lo aprendido en plantilla reutilizable.

### Matriz final 28/08

Decisión: `YA_CUBIERTO/CONSOLIDAR`.

La matriz mantuvo la misma idea y añadió el matiz operativo correcto: consolidar **cuando termine el lanzamiento**, no antes.

### Autoridad final humana + machine-readable

Estado final: `ALREADY_COVERED`.

Regla final:

> Launch-state/runbooks de Manecillas ya existen; convertir a plantilla reusable después del lanzamiento, no duplicar ahora.

## 3. Revalidación independiente

La revalidación independiente mantiene Q.4 sin corrección material. También insiste en una regla general del proyecto: documentación de preparación, configuración live y verificación E2E son estados distintos.

No aparece en las pasadas posteriores evidencia que justifique crear un segundo checklist paralelo.

## 4. Estado actual de `main`

La evidencia actual confirma que las autoridades base siguen existiendo.

### `docs/RELEASE-READINESS-V1.md`

Contiene, entre otros:

- inventario de rutas críticas;
- checks estáticos;
- builders/paridad;
- newsletter contracts;
- social-card checks;
- AI discoverability;
- procedimiento documentado de rollback;
- una advertencia explícita de que `STATIC_CHECKS_PASSED` no equivale a autorización de merge/deploy ni a QA completo de navegador.

### `docs/CONTENT-PARITY-MANECILLAS-V1.md`

Conserva la autoridad factual y de gating del lanzamiento de Manecillas:

- Monza Ediciones;
- publicación: **2026-09-03**;
- ISBN 979-8-90514-935-1;
- 272 páginas;
- PVP editorial 16 €;
- Paperback/tapa blanda;
- `purchaseUrl` todavía `null` en el corte documentado;
- tres fragmentos públicos;
- materiales de proceso preparados pero sujetos a gates;
- hub «Cómo se escribió» condicionado a notas reales;
- guía de club condicionada a activación posterior al lanzamiento;
- recursos de prensa/high-res condicionados a derechos/clearance;
- assets temporales solo mediante campaña/calendario.

## 5. Contexto temporal actual

Hoy es **29 de agosto de 2026**. La fecha editorial de publicación de *Las manecillas del recuerdo* es **3 de septiembre de 2026**, por lo que el lanzamiento todavía no ha ocurrido.

Esto importa metodológicamente: una plantilla «reutilizable» creada hoy solo podría capturar **lo que creemos que debe ocurrir**, no lo que realmente funcionó, falló, sobró o faltó durante el lanzamiento.

Por eso la decisión `ALREADY_COVERED/CONSOLIDATE_AFTER_LAUNCH` sigue siendo correcta.

## 6. Capas que la futura plantilla debe distinguir

Una checklist madura no puede mezclar estos estados:

### A. Verdad factual/editorial

- título;
- autor;
- editorial;
- ISBN;
- fecha;
- formato;
- páginas;
- PVP;
- retailer/URL solo si está verificado;
- derechos de fragmentos/assets.

Fuente: autoridad editorial, no campaña.

### B. Repositorio / artefacto público

- ficha de obra;
- JSON-LD y paridad visible;
- canonical/indexability;
- sitemap;
- redirects si existen migraciones reales;
- OG/social cards;
- navegación/interlinking;
- fragments/resources;
- feed/llms/AI surfaces según corresponda;
- accesibilidad/performance/security gates.

### C. Operación externa

- Search Console/Bing;
- IndexNow post-deploy si aplica;
- Brevo DOI/journeys/listas;
- campaña Metricool/redes;
- retailers/editorial;
- prensa/medios;
- perfiles/catálogos externos.

Git no puede declarar estas operaciones `CONFIGURED_LIVE` sin evidencia externa.

### D. Campaña temporal

- copies de lanzamiento;
- creatividades;
- calendario social;
- newsletters puntuales;
- eventos/firmas;
- assets «ya disponible».

No deben contaminar automáticamente contenido evergreen.

### E. Verificación y rollback

- smoke de producción;
- HTTP/canonical/sitemap;
- browser/mobile/a11y;
- newsletter E2E si se promete entrega;
- compra solo con destino real;
- observabilidad mínima;
- rollback target/procedure.

## 7. Gates que Manecillas ya ha enseñado a preservar

### Compra

PVP editorial ≠ `Offer` ni disponibilidad comercial. Un CTA de compra requiere destino verificable. Nunca derivar retailer de una búsqueda o asumir disponibilidad.

### Prensa

Tener imágenes no equivale a tener derecho de redistribución/high-res. El package de prensa debe pasar rights/clearance y builder/QA.

### Contenido derivado

«READY» no equivale a «PUBLICAR». Materiales de proceso, club o spoilers necesitan sus propios triggers editoriales.

### Newsletter

Código/arquitectura ≠ journey live ≠ entrega E2E. Cualquier promesa de lead magnet/serie debe probarse de extremo a extremo.

### Fechas

`dateModified` y copy temporal solo cambian por hechos/material changes, nunca por freshness hacks.

### Lanzamiento vs evergreen

Los assets/copies de campaña tienen ciclo de vida distinto a la ficha factual permanente.

## 8. Cuándo consolidar Q.4

Después del lanzamiento real, realizar un postmortem breve con evidencia:

1. qué gates se ejecutaron;
2. qué falló o requirió intervención manual;
3. qué checks fueron redundantes;
4. qué información faltó en el momento crítico;
5. qué operaciones externas no pudieron verificarse desde Git;
6. qué partes dependían específicamente de Manecillas y no son universales;
7. qué pasos deben ocurrir antes/durante/después del publication date;
8. qué rollback o smoke resultó útil.

Solo entonces extraer una plantilla genérica.

## 9. Forma recomendada de la futura plantilla

No crear una tercera fuente de hechos. La plantilla debería referenciar autoridades y estados, no copiar sus valores.

Posible estructura:

```text
PREPARE
  facts_locked
  rights_locked
  content_ready
  schema_parity
  redirects_if_needed
  accessibility/performance/security

PRELAUNCH_EXTERNAL
  retailer_verified
  newsletter_e2e
  press_clearance
  webmaster properties

PUBLISH
  public artifact
  sitemap/canonical
  release verify
  post-deploy indexing notification

CAMPAIGN
  email/social/events

POSTLAUNCH
  live facts check
  conversion destination check
  external parity
  postmortem
  reusable learnings
```

Cada item debería registrar owner/evidence/status cuando sea necesario.

## 10. Anti-patrones

No:

- crear `LAUNCH-CHECKLIST-V2/V3` paralelos;
- copiar ISBN/PVP/fecha en múltiples runbooks;
- marcar tareas externas como hechas porque existe código;
- publicar recursos gated para completar la checklist;
- inventar retailer para que el lanzamiento «esté completo»;
- hacer depender un futuro lanzamiento de pasos específicos de Manecillas;
- convertir una checklist en autorización automática de merge/deploy.

## 11. Definition of Done de la consolidación futura

- el lanzamiento de Manecillas ya ocurrió;
- existe postmortem basado en evidencia real;
- la plantilla distingue factual / repo / external / campaign / E2E;
- reutiliza las autoridades existentes;
- no duplica valores factuales;
- tiene estados explícitos, incluyendo blocked/not-applicable/no-data;
- incorpora derechos y comercio como gates;
- incorpora rollback y verificación post-deploy;
- cualquier operación externa exige evidencia externa;
- se prueba la plantilla contra Manecillas como caso histórico y, cuando exista, contra un segundo lanzamiento.

## 12. Relaciones

- **C.1:** campaña editorial Manecillas; Q.4 no crea un segundo calendario.
- **H.1/H.2:** automatizaciones Brevo requieren E2E antes de declararse listas.
- **K.1/K.3:** venta/afiliación solo con operación comercial real.
- **M.1/M.3:** seguridad live forma parte del release gate, no de los facts del libro.
- **Q.2:** GSC/Bing son operaciones externas.
- **Q.3:** un experimento no es una checklist de lanzamiento.

## 13. Conclusión

Q.4 está `ALREADY_COVERED`. El proyecto ya posee las autoridades y runbooks que una checklist paralela intentaría duplicar. Como el lanzamiento de Manecillas sigue siendo futuro a 29/08/2026, la acción correcta es ejecutar las autoridades actuales y, después del 03/09, extraer de la evidencia real una plantilla reusable. Así se conserva aprendizaje sin crear otra fuente de verdad antes de saber qué ocurrió realmente.