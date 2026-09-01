# D.8 · Modo oscuro manual persistente

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `DEFER`.

## 1. Hipótesis original

Añadir un toggle manual persistente de modo oscuro mediante `localStorage`, incluso si el sitio ya respeta o puede respetar `prefers-color-scheme`, para permitir forzar una apariencia distinta del sistema operativo.

## 2. Evolución histórica

### Revisión → `DEFER`

#135 concluye que es una tendencia genérica, no una fricción prioritaria. Reabrir solo cuando la dirección visual/tokens estén estabilizados y exista demanda.

### Matriz → `DEFERIR`

> «Dark-mode toggle solo por demanda. No añadir segundo sistema visual en plena estabilización de diseño.»

### Autoridad final → `DEFER`

> «Dark-mode manual implica mantener otro sistema visual; reevaluar solo con demanda.»

### Revalidación independiente

D.1–D.12 se mantienen. No aparece evidencia que convierta dark mode en prioridad.

## 3. Coste real de un segundo sistema visual

Un toggle no es solo dos variables de color. Afecta:

- tokens de texto/fondo/borde;
- portadas/fotografía/ilustraciones;
- logos e iconos;
- estados hover/focus/disabled/error;
- formularios;
- diálogo Explorar/asistente;
- embeds/media;
- tablas;
- tooltips/modales;
- print;
- forced colors/high contrast;
- screenshots/QA visual;
- CSP solo indirectamente si se introdujera JS inline, que no debe hacerse.

## 4. Persistencia

`localStorage` añade estado persistente y lógica de arranque:

- evitar flash de tema incorrecto;
- sincronizar con preferencia del sistema cuando no hay override;
- permitir volver a «usar sistema»;
- no dejar estado corrupto;
- considerar varias pestañas.

Nada de esto está justificado sin demanda.

## 5. Apariencia ≠ accesibilidad

Dark mode no debe venderse como una «función accesible» universal.

La quinta pasada añadió R.13 `prefers-contrast: more` como auditoría accesible y R.8 Forced Colors en otra línea. Son necesidades distintas:

- dark mode = apariencia/luminancia elegida;
- prefers-contrast = preferencia por más contraste authored;
- forced colors = colores del sistema impuestos por el usuario.

No usar D.8 como sustituto de accesibilidad real.

## 6. Relación con D.2/F.5

D.2 rechaza Reader Mode propio y F.5 rechaza texto-grande propio porque multiplican estados cuando la base debe ser robusta.

D.8 sigue el mismo principio: primero estabilizar un sistema visual excelente y compatible con preferencias nativas; después añadir un override solo si hay una necesidad demostrada.

## 7. Si algún día se reabre

Modelo de preferencia recomendado:

```text
SYSTEM
LIGHT
DARK
```

No un booleano simple si se quiere respetar sistema y override manual.

La clase/atributo debería aplicarse antes del paint cuando sea posible, pero sin introducir JS inline incompatible con CSP.

## 8. Arquitectura futura correcta

- tokens semánticos, no colores hardcodeados por componente;
- un único source of truth del tema;
- componentes sin CSS duplicado completo;
- assets con variantes solo donde sea realmente necesario;
- control accesible con nombre/estado claro;
- `color-scheme` coherente para controles nativos si procede;
- tests de contraste por tema;
- QA móvil/desktop.

## 9. Gate de reapertura

```text
visual system stabilized
AND repeated user demand
AND token coverage sufficient
AND QA capacity for both themes
AND no regressions in contrast/brand/readability
```

Podría añadirse evidencia analítica cualitativa, pero no es necesario rastrear preferencias personales para decidir.

## 10. Qué NO hacer

- añadir toggle porque «todas las webs modernas lo tienen»;
- duplicar hojas CSS enteras;
- usar `filter: invert()` global;
- persistir más datos de los necesarios;
- asumir dark = high contrast;
- romper imágenes/logos;
- crear flash de tema al cargar;
- sumar dark mode, reader mode y texto grande como paquete sin investigación.

## 11. Revalidación del repo actual

No se ha localizado en el corte actual una función manual/persistente equivalente que obligue a reclasificar D.8 como `ALREADY_COVERED`.

Eso no cambia el veredicto: **no implementada + `DEFER` no significa deuda urgente**.

## 12. Pasadas posteriores revisadas

- R.13 `prefers-contrast: more` añade un enfoque de auditoría sobre preferencias del sistema, no un tema nuevo;
- Forced Colors refuerza que accesibilidad debe probar preferencias nativas;
- resto de pasadas cuarta–decimoquinta no cambia D.8.

## 13. Trazabilidad

- lista inicial — toggle manual persistente;
- revisión — `DEFER`;
- matriz — `DEFERIR`;
- autoridad final — `DEFER`;
- revalidación independiente — mantenida;
- R.13/Forced Colors — límites conceptuales.

## 14. Definition of Done de esta reconstrucción

- [x] estado defer preservado;
- [x] coste de segundo sistema visual detallado;
- [x] apariencia vs accesibilidad separadas;
- [x] gate futuro definido;
- [x] sin implementación prematura.

## Recomendación para Clara/Claude

No implementar D.8 ahora. Mantener el sistema visual único y robusto; reevaluar un selector `system/light/dark` únicamente con demanda real y tokens suficientemente estables.