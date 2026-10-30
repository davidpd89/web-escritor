# Encargo: homogeneizar tipografía de campos editables en móvil

Estado: **PENDIENTE DE IMPLEMENTACIÓN — PR EN BORRADOR**.
Prioridad: P2, coherencia visual/usabilidad. Riesgo de zoom iOS por verificar.
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Evidencia medida, no hipótesis

El 30/10 se inspeccionó producción con Chromium/Playwright: viewport 390 × 844,
movimiento reducido, service workers bloqueados, peticiones ajenas al origen
bloqueadas y sin enviar formularios. Valores de `getComputedStyle().fontSize`:

| Ruta | Campo | Tamaño |
|---|---|---|
| `/cuaderno/que-es-el-portal-fantasy/` | `#nl-email-cuaderno` inline | 16 px |
| misma página, popup abierto mediante scroll | `#nl-popup-email` | 15,2 px |
| `/herramientas/distribucion-pov/` | `#pov-format-mode` | 15,2 px |
| misma herramienta | `#pov-input` | 16,32 px |
| `/herramientas/personajes/` | `#map-title`, `#character-name`, `#relation-label` | 15,2 px |
| misma herramienta | `#relation-from`, `#relation-to`, `#relation-type` | 15,2 px |
| misma herramienta | `#relation-evolution` | 14,72 px |
| `/recomendaciones/` | campo de búsqueda | 16 px |

Todos usan la familia UI Manrope, salvo el textarea principal POV, que usa la
familia de lectura Newsreader. Esa distinción funcional no es un error por sí misma.

Reglas fuente actuales:

- `assets/newsletter-popup.css:10`: `#nl-popup-email`, `.95rem`.
- `assets/v1-tools.css:20`: `.tool-textarea--small`, `.92rem`.
- `assets/v1-tools.css:29`: `.tool-select`, `.95rem`.
- `assets/v1-tools.css:89`: `.tool-input`, `.95rem`.
- `assets/mapa-personajes.css:8`: variante `.map-canvas-head .tool-select`, `.88rem`;
  inventariar si está visible y qué sobreescritura gana antes de modificarla.

## Qué NO se ha demostrado

No se ha probado Safari físico ni se ha medido su autozoom al enfocar. El posible
zoom automático de campos menores de 16 px es una hipótesis de compatibilidad,
no un fallo iOS confirmado. No presentarlo como incumplimiento WCAG automático.
No usar Chromium móvil como sustituto de esa evidencia.

El pendiente `docs/pending/zoom-text-resilience-followups.md` trata overflow del
masthead y CLS de portada; son problemas distintos, fuera de este encargo.

## Encargo a la IA implementadora

1. Repetir las mediciones y censar controles editables visibles en las familias
   de formularios/herramientas; excluir honeypots, inert, ocultos y checkbox/radio.
2. Elegir una política compartida para tamaño de entrada móvil, con mínimo
   efectivo de 16 px bajo configuración base y compatible con texto ampliado.
3. Mantener jerarquía editorial y distinción entre UI y lectura. No hacer una
   sustitución indiscriminada de todos los tamaños pequeños de la web.
4. Resolver reglas en origen/tokens compartidos sin acumular overrides por página.
5. Validar foco, teclado virtual, visualViewport, reflow y contenido largo;
   preservar funcionamiento del popup y tamaño/etiquetas de los controles.
6. Si se cambian recursos registrados: versionado, hashes, paridad de generadores
   e índice Pagefind actualizados según los contratos vigentes.

## Criterios de aceptación

- [ ] Inventario antes/después de controles editables y estilos calculados.
- [ ] Tamaño coherente en los campos enumerados a 320/390/768 px.
- [ ] Sin bloquear zoom del usuario: no añadir `user-scalable=no` ni límites equivalentes.
- [ ] Regresión de tamaño efectivo y reflow, no solo búsqueda de cadenas CSS.
- [ ] Pruebas newsletter y herramientas pasan; screenshots antes/después móvil y escritorio.
- [ ] Safari físico: aportar evidencia de enfoque/teclado; si no está disponible,
      declarar esa parte no verificada sin inventar el resultado.
- [ ] CI, accesibilidad, presupuestos y baseline visual validados antes del deploy.

Esta PR solo contiene el encargo. Otra IA continúa esta rama con diseño, código,
pruebas y publicación; no fusionar como si el trabajo ya estuviera realizado.