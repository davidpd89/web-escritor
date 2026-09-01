# D.11 — Estados vacíos, no-results y unavailable states

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`IMPLEMENT_AFTER_CURRENT_DEBT`**

## 1. Propósito

Este documento reconstruye directamente la investigación completa de D.11 en PR #135: inventariar y mejorar estados vacíos, sin resultados, indisponibles y de error para que no se conviertan en callejones sin salida.

No parte de #148 como autoridad primaria. Recupera la idea original, las revisiones sucesivas, el criterio de producto, los límites de accesibilidad y la situación actual del repositorio.

Esta PR es **docs-only**. No cambia todavía el copy ni los componentes productivos.

## 2. Veredicto

D.11 sigue siendo trabajo neto y conserva **`IMPLEMENT_AFTER_CURRENT_DEBT`**.

La tarea correcta no es “crear un componente EmptyState” ni asumir que todos los estados actuales están mal. Es realizar un inventario de superficies reales y corregir únicamente las que no explican:

- qué ocurrió;
- si es temporal o definitivo;
- qué puede hacer la persona a continuación;
- cómo recuperar el flujo sin trampas ni presión comercial.

## 3. Hipótesis original

En la lista original de 108 ideas, D.11 proponía revisar casos como:

- buscador sin resultados;
- club de lectura sin comentarios;
- recursos aún no disponibles;
- cualquier panel/listado sin contenido.

La tesis era simple: un estado vacío debe ayudar a continuar, no dejar una zona muerta.

A diferencia de varias ideas D orientadas a ornamentación, #135 consideró que esta sí ataca fricción real y tiene coste relativamente bajo.

## 4. Evolución histórica

| Fase | Estado | Interpretación |
|---|---|---|
| Idea original | propuesta | Convertir empty states en puntos de orientación. |
| Revisión 108/108 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Inventario de no-results/error/empty states con acción útil, foco y copy. |
| Matriz intermedia | `IMPLEMENTAR` | Explicar siguiente acción; evitar dark patterns. |
| Autoridad final #135 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Auditoría transversal pendiente, no feature decorativa. |
| Revalidación independiente | mantenida | No se detecta motivo para retirar la mejora. |
| `main` actual | sigue pendiente como auditoría | Hay estados individuales, pero no evidencia de un contrato/inventario global que cierre D.11. |

No existe contradicción sustantiva entre las fases: cambia la etiqueta operativa, no la dirección.

## 5. Qué significa “estado vacío” en esta idea

D.11 no se limita a listas con cero elementos. Incluye familias distintas:

### 5.1 Sin resultados

Ejemplos:

- búsqueda sin coincidencias;
- filtro que deja cero elementos;
- herramienta que no detecta incidencias.

Debe diferenciarse “no encontramos nada” de “la operación falló”.

### 5.2 Sin contenido todavía

Ejemplos:

- sección futura sin publicaciones;
- club sin comentarios;
- historial sin entradas.

No debe fingirse actividad inexistente.

### 5.3 Indisponible temporalmente

Ejemplos:

- recurso aún no publicado;
- servicio externo no accesible;
- acción desactivada en staging.

La UI debe explicar la condición real y, si existe, una alternativa.

### 5.4 Error recuperable

Ejemplos:

- red caída;
- timeout;
- validación fallida;
- respuesta inesperada.

Debe incluir recovery razonable y no transformar cualquier error en “suscríbete”.

### 5.5 Resultado legítimamente vacío

Una herramienta puede devolver cero incidencias porque el texto está bien. Ese estado es éxito, no error.

## 6. Criterios que #135 preserva

### 6.1 Siguiente acción útil

Un buen estado puede ofrecer:

- ajustar consulta;
- limpiar filtro;
- volver a un hub;
- probar una ruta relacionada;
- reintentar cuando el error es recuperable;
- consultar una explicación.

No hace falta añadir CTA si no existe una siguiente acción honesta.

### 6.2 Sin dark patterns

#135 fue explícita en no usar el vacío como excusa para empujar conversiones.

Incorrecto:

> No hay resultados. Suscríbete a la newsletter.

si la newsletter no resuelve la consulta.

Correcto:

> No encontramos resultados para esa búsqueda. Prueba con menos términos o vuelve al índice del Cuaderno.

### 6.3 Foco y accesibilidad

Cuando el estado aparece tras una acción dinámica debe revisarse:

- anuncio mediante `role=status`/`aria-live` solo donde corresponda;
- no mover foco arbitrariamente;
- mantener el control que originó la acción accesible;
- error asociado al campo si el problema es de validación;
- retry operable con teclado;
- no depender solo de color/icono.

La investigación de F.4/F.6 refuerza estos requisitos.

## 7. Por qué no se convierte en un “sistema universal” de inmediato

Las superficies no comparten necesariamente la misma semántica.

Un único componente genérico podría mezclar:

- error de red;
- cero resultados;
- contenido futuro;
- éxito con cero incidencias;
- feature deshabilitada.

Primero se necesita un inventario y taxonomía. Después se puede extraer una pieza compartida si hay repetición real.

## 8. Reconciliación con `main`

La revisión actual encuentra múltiples patrones de estados y mensajes en el repositorio, por ejemplo formularios y runtime con mensajes de error/éxito. Eso demuestra que existe trabajo local, **no que D.11 esté cerrado**.

No se ha identificado una autoridad transversal equivalente a:

```text
surface
stateKind
trigger
message
primaryRecovery
secondaryRecovery
focusPolicy
announcementPolicy
owner
verifiedAt
```

Tampoco debe inferirse por grep que todo estado no encontrado está mal: el objetivo de D.11 es auditar journeys reales.

## 9. Inventario mínimo propuesto por #135 reconstruido

La futura auditoría debería cubrir, como mínimo:

### Búsqueda / asistente

- consulta vacía;
- consulta sin resultados;
- Pagefind no disponible y fallback;
- error inesperado;
- offline.

### Newsletter / formularios

- email inválido;
- staging deshabilitado;
- timeout;
- rate limit;
- servidor/worker no disponible;
- confirmación pendiente.

### Club/comunidad

- cero comentarios;
- sesión sin eventos próximos;
- contenido todavía no publicado.

### Herramientas

- input vacío;
- resultado cero válido;
- tamaño/entrada inválida;
- procesamiento que falla;
- feature no compatible.

### Archivos y listados editoriales

- no hay eventos futuros;
- filtro de recomendaciones vacío;
- categoría sin contenido;
- recurso retirado/no disponible.

## 10. Auditoría propuesta

Para cada estado real:

| Campo | Pregunta |
|---|---|
| `surface` | ¿En qué ruta/componente aparece? |
| `trigger` | ¿Qué acción lo genera? |
| `kind` | empty / no-results / unavailable / error / success-empty |
| `copy` | ¿Describe correctamente lo ocurrido? |
| `nextAction` | ¿Existe una recuperación útil? |
| `a11y` | ¿Se anuncia/recorre correctamente? |
| `mobile` | ¿Sigue siendo usable en viewport pequeño? |
| `analytics` | ¿Hace falta medirlo o sería tracking inútil? |
| `owner` | ¿Qué autoridad produce el estado? |

## 11. No hacer

D.11 no autoriza:

- CTA comercial en todos los vacíos;
- popups de newsletter por “no results”;
- inventar contenido de relleno;
- ocultar que algo no está disponible;
- mensajes vagos “Algo salió mal” cuando existe un código accionable;
- auto-retry infinito;
- mover foco al `<body>`;
- añadir `aria-live` indiscriminadamente;
- duplicar mensajes que ya produce una autoridad existente;
- transformar cada ausencia en una tarjeta visual grande.

## 12. Relación con D.5

Pagefind ya está implementado. D.11 no debe crear otro motor de búsqueda: debe evaluar la experiencia cuando Pagefind devuelve cero resultados o no puede cargarse.

## 13. Relación con D.4

Si algún día existe “leer después”, su lista vacía sería un caso D.11. Eso no justifica implementar D.4 antes de que haya demanda.

## 14. Relación con J / comunidad

Un club sin comentarios no debe simular comunidad. Puede explicar que aún no hay intervenciones y ofrecer el mecanismo real para participar, si existe.

## 15. Relación con accesibilidad

D.11 se cruza especialmente con:

- F.4 focus visible / Focus Not Obscured;
- F.6 estados dinámicos del asistente;
- mensajes de formularios con `role=status`;
- journeys keyboard/browser.

Pa11y verde por sí solo no demuestra que un estado dinámico tenga una recuperación comprensible.

## 16. Blueprint operativo futuro

Cuando se ejecute D.11:

1. enumerar las familias de producto;
2. navegar journeys reales, no solo grep;
3. registrar estados existentes;
4. clasificar semántica;
5. priorizar callejones sin salida y errores frecuentes;
6. corregir copy/acción/foco mínimo;
7. extraer componente solo si aparece repetición genuina;
8. probar desktop/móvil/teclado;
9. conservar screenshots o fixtures en casos relevantes;
10. no aumentar tracking salvo una pregunta de producto concreta.

## 17. Criterio de prioridad

Prioridad alta dentro de la auditoría:

```text
usuario pierde trabajo
> acción principal queda bloqueada
> no entiende qué ocurrió
> no puede recuperarse
> estado meramente poco elegante
```

Esto evita convertir D.11 en una campaña de microcopy cosmético.

## 18. DoD de futura implementación

- inventario de superficies relevantes;
- estados clasificados por semántica;
- top callejones sin salida corregidos;
- recovery real cuando existe;
- no dark patterns;
- foco/anuncio revisados en estados dinámicos;
- mobile/reflow comprobado;
- tests solo donde el contrato pueda regresionar;
- documentación de excepciones deliberadas;
- ninguna autoridad paralela innecesaria.

## 19. Pasadas tardías

Las pasadas posteriores de #135 no revierten D.11. Las investigaciones de accesibilidad, QA de navegador y privacidad refuerzan el enfoque audit-first y el rechazo a interacciones manipulativas.

La revalidación independiente mantiene D.11 dentro del conjunto de decisiones D válidas.

## 20. Estado de verdad

- `DOCUMENTED`: sí, esta PR.
- `IMPLEMENTED_IN_PR`: no.
- `MERGED_MAIN`: no mientras la PR esté abierta.
- `CONFIGURED_LIVE`: no; no se ha ejecutado una auditoría live completa aquí.
- `VERIFIED_E2E`: no.

No se debe confundir la existencia de mensajes individuales en `main` con cierre de la auditoría transversal.

## 21. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- investigaciones posteriores de accesibilidad/UX de #135.

## 22. Conclusión

D.11 conserva **`IMPLEMENT_AFTER_CURRENT_DEBT`**. La mejora no consiste en decorar pantallas vacías, sino en identificar estados reales donde una persona queda sin explicación o siguiente paso y corregirlos con semántica, recuperación y accesibilidad apropiadas. La presencia de algunos mensajes correctos en el sitio no sustituye esa auditoría sistemática.