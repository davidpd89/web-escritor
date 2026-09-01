# D.1 · Micro-interacciones de confirmación

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.  
Revalidación actual: el repo ya contiene microfeedback funcional en acciones concretas; no abrir un «proyecto de animaciones» global.

## 1. Hipótesis original

La lista inicial proponía pequeñas animaciones/feedback al completar acciones —suscripción, guardar, copiar, etc.— con atención explícita a `prefers-reduced-motion` y al histórico de CLS del proyecto.

La idea válida no era añadir movimiento por estética, sino **hacer visible el cambio de estado**.

## 2. Evolución en #135

### Revisión → `CONDITIONAL`

La primera revisión rebaja el valor general de la idea:

- bajo coste;
- bajo valor si es decorativa;
- solo procede cuando comunica éxito, error o estado.

### Matriz → `PILOTAR`

La matriz permite pilotos acotados:

> «Microfeedback donde confirme una acción; no animación decorativa. Reduced motion y cero CLS obligatorios.»

### Autoridad final → `CONDITIONAL`

El cierre conserva exactamente esa frontera:

> «Microfeedback solo para confirmar acciones; `prefers-reduced-motion` y cero CLS.»

### Revalidación independiente

D.1–D.12 fueron mantenidas. No aparece justificación para convertir D.1 en una capa visual sitewide.

## 3. Qué problema resuelve

Casos válidos:

- indicar «Copiado» tras copiar una bio/enlace;
- indicar envío/espera/éxito/error en formularios;
- confirmar una preferencia guardada;
- mostrar estado loading cuando la acción tarda;
- feedback de validación accesible.

Casos inválidos:

- animar botones solo porque «se siente premium»;
- introducir confetti, rebotes o transiciones globales sin función;
- hacer depender la comprensión del color/movimiento;
- animar layout y provocar CLS.

## 4. Revalidación del repo actual

`script.js` ya ofrece ejemplos reales que materializan D.1:

### Copiar bio en prensa

El botón `.copy-btn` cambia temporalmente a:

```text
✓ Copiado
```

Eso confirma una acción real sin navegación adicional.

### Newsletter

El flujo actual expone:

- «Enviando…»;
- validación de email;
- error de red/timeout/rate limit;
- confirmación pendiente DOI;
- estado específico de staging.

Son microfeedback funcional, no decoración.

### Movimiento reducido

El botón «Volver arriba» comprueba:

```js
matchMedia('(prefers-reduced-motion: reduce)')
```

y cambia smooth scroll por comportamiento inmediato.

Conclusión: D.1 está **parcialmente materializada por componentes** aunque históricamente siga `CONDITIONAL` como idea de expansión. No crear una nueva librería de motion.

## 5. Contrato de accesibilidad

Todo estado nuevo debe tener una vía perceptible adecuada:

- texto visible cuando el mensaje importa;
- `role=status` / `aria-live` solo cuando corresponde;
- no añadir regiones live duplicadas;
- foco no debe saltar sin necesidad;
- error no depender solo de rojo;
- acción reversible o clara cuando proceda.

F.6 ya advierte que añadir ARIA indiscriminadamente puede duplicar anuncios. D.1 debe reutilizar la semántica existente.

## 6. Reduced motion

El gate no consiste en «tener una media query en algún CSS». Para cualquier transición relevante:

- la acción debe funcionar sin animación;
- `prefers-reduced-motion: reduce` debe eliminar/reducir movimiento no esencial;
- no usar parallax/scroll effects para comunicar estado;
- ninguna animación debe bloquear interacción.

## 7. Cero CLS

Feedback de confirmación debe reservar espacio o sustituir contenido dentro de un control estable.

Evitar:

- insertar banners arriba del contenido que desplazan todo;
- cambiar dimensiones de botones de forma brusca;
- añadir success cards que mueven el viewport sin intención;
- loaders que alteran el layout.

Preferir:

- texto dentro del control con ancho razonablemente estable;
- región de estado ya reservada;
- overlays solo cuando el patrón de interacción lo exige y está bien gestionado.

## 8. Performance/INP

D.1 no justifica frameworks ni runtime adicional.

Regla:

```text
CSS / DOM mínimo existente
> nueva dependencia de animación
```

Los handlers deben ser pequeños; si el feedback se produce tras una tarea pesada, el problema principal puede ser INP/algoritmo, no la animación.

## 9. Criterio de aceptación de una nueva microinteracción

Debe responder «sí» a:

1. ¿qué acción o estado confirma?
2. ¿sin feedback el usuario puede dudar?
3. ¿funciona sin movimiento?
4. ¿no introduce CLS?
5. ¿no duplica una región de estado existente?
6. ¿no añade una dependencia?
7. ¿mantiene teclado/lector de pantalla?

Si no hay respuesta concreta al punto 1, no implementar.

## 10. Relación con otras ideas

- D.3: una barra de progreso es estado continuo de lectura, no microfeedback de acción.
- D.4: si algún día existe read-later, D.1 puede confirmar «Guardado», pero no justifica construir D.4.
- F.4/F.6: foco y anuncios accesibles prevalecen sobre estética.
- E.2: no degradar INP.

## 11. Qué NO hacer

- librería de animación global;
- confetti en suscripción;
- hover-only feedback;
- animar por métricas de «engagement»;
- microinteracciones que oculten errores;
- loops permanentes;
- transiciones que ignoren reduced motion;
- cambiar `aria-live` para «hacer más accesible» sin journey real.

## 12. Pasadas posteriores revisadas

Las pasadas cuarta a decimoquinta no cambian el estado de D.1. R.12 sobre LoAF/`scheduler.yield()` refuerza medir trabajo bloqueante antes de añadir runtime; R.13 trata contraste, no motion. No existe un override posterior que convierta D.1 en implementación general.

## 13. Trazabilidad

- lista inicial #135 — hipótesis;
- revisión 108/108 — `CONDITIONAL`;
- matriz final — `PILOTAR` acotado;
- autoridad final — `CONDITIONAL`;
- revalidación independiente — mantenida;
- `script.js` actual — evidencia de microfeedback funcional ya existente.

## 14. Definition of Done de esta reconstrucción

- [x] propósito funcional separado de animación decorativa;
- [x] evolución de estados preservada;
- [x] reduced motion/CLS/accessibility documentados;
- [x] ejemplos reales actuales identificados;
- [x] no se propone framework o sistema paralelo.

## Recomendación para Clara/Claude

No implementar D.1 como feature global. Añadir microfeedback únicamente junto a una acción que realmente necesite confirmación y bajo los gates de accesibilidad, reduced motion y estabilidad visual.