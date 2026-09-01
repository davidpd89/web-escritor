# B.8 · Resúmenes TL;DR en artículos largos

Fecha de reconstrucción: 2026-08-29

Idea original: incorporar un resumen breve al inicio de artículos largos del Cuaderno para mejorar escaneabilidad y facilitar extracción de los puntos centrales.

Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.

Estado final: `CONDITIONAL`.

## Veredicto reconciliado

**CONDITIONAL. TL;DR SOLO EN PIEZAS LARGAS/PRÁCTICAS DONDE MEJORE LA EXPERIENCIA DEL LECTOR; NO COMO PLANTILLA GEO/AEO OBLIGATORIA.**

#135 mantuvo la utilidad potencial de un resumen al principio, pero fue retirando cualquier interpretación de que las IA “necesiten” ese bloque. La guía oficial de Google de 2026 refuerza la decisión: no hay que chunkear ni reescribir el contenido con un formato especial para AI Overviews/AI Mode.

## 1. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` propuso un bloque TL;DR breve al inicio de artículos largos del Cuaderno, con doble objetivo:

- lectura rápida/escaneabilidad;
- facilitar que motores de respuesta identifiquen los puntos principales.

La hipótesis debía validarse editorialmente, no convertirse en una transformación masiva.

## 2. Evolución cronológica en #135

### 2.1 · Revisión exhaustiva → `CONDITIONAL`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` mantuvo B.8 únicamente para guías largas donde mejore la escaneabilidad. Rechazó convertirlo en una plantilla “GEO”.

### 2.2 · Matriz final → `PILOTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` dejó un piloto pequeño:

- TL;DR en guías/artículos largos;
- solo si ayuda al lector;
- no en todas las piezas.

### 2.3 · Autoridad final → `CONDITIONAL`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó la decisión definitiva:

> TL;DR únicamente en piezas largas/prácticas donde mejora lectura; no como plantilla obligatoria para IA.

### 2.4 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` mantuvo B.8 y volvió a apoyarse en la guía oficial Google 2026: SEO clásico y contenido people-first siguen siendo la base; no existe una obligación de estructurar el texto específicamente para IA.

Secuencia:

```text
hipótesis: resumen breve mejora lectura + extracción
→ revisión: CONDITIONAL, solo guías largas
→ matriz: PILOTAR con alcance pequeño
→ Google 2026: no chunking/formato especial para IA
→ autoridad final: CONDITIONAL
→ revalidación: mantiene
```

## 3. Fuentes primarias revalidadas

Google Search Central:

- AI features and your website: https://developers.google.com/search/docs/appearance/ai-features
- Optimizing for generative AI features: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Helpful, reliable, people-first content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Principios aplicables:

- no hay requisitos técnicos/editoriales adicionales específicos para AI Overviews/AI Mode;
- no hace falta dividir artificialmente contenido en fragmentos pequeños;
- no hace falta reescribir con un estilo especial para sistemas generativos;
- la organización clara y útil para personas sigue siendo válida;
- las features de IA pueden usar múltiples consultas/fuentes, por lo que un TL;DR no es una “llave” de citación.

## 4. Diferencia entre B.8 y B.3

Las dos ideas deben mantenerse separadas:

### B.3 — respuesta directa local

Responde al inicio de una **sección/pregunta concreta**. Ejemplo: «¿Qué es portal fantasy?».

### B.8 — resumen de pieza completa

Sintetiza los principales puntos de un **artículo largo entero**.

Un artículo puede necesitar uno, ambos o ninguno. No inferir que todo contenido con H2 debe tener respuesta directa ni que todo contenido largo necesita TL;DR.

## 5. Dónde sí puede aportar

Candidatos naturales:

- guía extensa de editoriales;
- artículo práctico de worldbuilding;
- tutorial largo de una herramienta;
- comparación/metodología con varios pasos;
- explicación factual extensa donde el lector necesita primero una orientación.

El resumen debería permitir decidir rápidamente:

- si el artículo responde a lo que busca;
- cuáles son sus 3–5 ideas centrales;
- qué acción/lectura seguir.

## 6. Dónde no usarlo por defecto

- fragmentos de novela;
- relato/ensayo cuya experiencia depende de la progresión;
- página Autor;
- ficha de libro corta;
- entrevistas narrativas;
- páginas donde ya hay una entradilla que cumple la misma función;
- artículos suficientemente breves;
- cualquier pieza donde el bloque repita literalmente la introducción.

## 7. No establecer un umbral de palabras arbitrario como ley

#135 no demostró que “más de X palabras = TL;DR obligatorio”.

La decisión debe usar señales editoriales:

- longitud real;
- complejidad;
- intención de consulta;
- estructura;
- necesidad de escaneabilidad;
- feedback/queries de lectores.

Puede existir una heurística interna para descubrir candidatos, pero no debe fallar CI ni producir bloques automáticamente.

## 8. Patrón editorial recomendado si se pilota

Ejemplo simple:

```html
<aside class="article-summary" aria-labelledby="summary-title">
  <h2 id="summary-title">En pocas palabras</h2>
  <ul>
    <li>Punto central 1.</li>
    <li>Punto central 2.</li>
    <li>Punto central 3.</li>
  </ul>
</aside>
```

No es obligatorio usar `aside`; puede ser una entradilla normal si encaja mejor en el diseño. La semántica debe seguir la intención real, no un patrón pensado para bots.

## 9. Requisitos de calidad

Un buen TL;DR:

- está escrito/revisado por humano;
- no introduce hechos que el artículo no sustenta;
- puede entenderse sin contexto excesivo;
- no sustituye el análisis original;
- no repite 5 veces las mismas keywords;
- conserva tono editorial;
- enlaza a secciones solo si mejora navegación;
- sigue siendo correcto después de actualizar el artículo.

Si el artículo cambia materialmente, el resumen forma parte del contenido que debe revisarse.

## 10. Piloto recomendado

1. seleccionar 3–5 artículos realmente largos/prácticos;
2. verificar que la entradilla actual no cubre ya la necesidad;
3. registrar objetivo: escaneabilidad/comprensión, no “subir GEO”;
4. crear resumen manual de 3–5 puntos o 1–2 párrafos;
5. comprobar móvil, 200% texto, screen reader/heading order y print si procede;
6. observar interacción/búsquedas/feedback disponible;
7. extender solo si mejora la experiencia.

No atribuir una futura cita de IA al TL;DR sin un diseño experimental mucho más fuerte.

## 11. Relación con contenido citable

Un resumen claro puede convertirse en un pasaje citable porque expresa el contenido con precisión. El mecanismo legítimo es **claridad**, no manipulación de la extracción.

La ventaja competitiva debe seguir estando en:

- experiencia propia;
- información factual original;
- ejemplos de David/obras/herramientas;
- fuentes bien verificadas;
- análisis que no sea commodity.

## 12. Qué NO hacer

- insertar TL;DR automáticamente en todos los artículos;
- generar el resumen con IA y publicarlo sin revisión;
- ocultar bloques para humanos y mostrar otros a bots;
- repetir title/meta description como TL;DR;
- usar “AI Summary” si no existe una razón de producto;
- convertirlo en una lista fija de keywords;
- cambiar la voz literaria del Cuaderno por una plantilla uniforme;
- hacer de su presencia un gate SEO;
- medir éxito por número de artículos con TL;DR.

## 13. QA si se implementa

Automatizable:

- HTML válido;
- heading order;
- IDs únicos;
- no duplicar el componente;
- reflow/sitewide accessibility;
- enlaces internos válidos;
- no oculto mediante CSS solo para crawlers.

No automatizable de forma fiable:

- si resume bien;
- si aporta información;
- si conserva voz;
- si la pieza realmente lo necesita.

Esos puntos requieren revisión editorial.

## 14. Coste / beneficio

Coste: bajo por artículo, pero alto si se convierte en obligación de mantenimiento sitewide.

Beneficio: medio cuando el contenido es extenso/práctico y el usuario necesita escanear; bajo o negativo en piezas literarias/narrativas.

Por eso `CONDITIONAL` sigue siendo el estado correcto.

## 15. Definition of Done

### Historia recuperada

- [x] hipótesis original;
- [x] revisión `CONDITIONAL`;
- [x] matriz `PILOTAR`;
- [x] autoridad final `CONDITIONAL`;
- [x] revalidación independiente;
- [x] Google 2026 sobre no-chunking/no-formato especial;
- [x] diferencia B.3/B.8 preservada.

### Piloto futuro

- [ ] candidatos seleccionados por utilidad real;
- [ ] resumen humano;
- [ ] QA mobile/a11y;
- [ ] revisión de resultados;
- [ ] sin conversión a plantilla global sin evidencia.

## 16. Trazabilidad de #135

Aportan contenido específico:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/ai-discoverability/04-CONTENIDO-CITABLE-Y-RECOMENDABLE.md` como contexto editorial.

Las pasadas/overrides/blueprints restantes se revisaron y no cambian el estado final de B.8.

## 17. Recomendación

**MERGE como reconstrucción completa + `CONDITIONAL`.** TL;DR se aplica donde mejora de verdad la lectura, no para satisfacer una checklist de IA.