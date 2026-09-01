# F.5 · Revalidación de producción — modo de texto grande propio

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `REJECT · NATIVE_RESIZE_PREFERRED · F1_F2_ARE_THE_CORRECT_CONTRACT · NO_CODE`

## 1. Conclusión

Se mantiene el rechazo de un toggle persistente de «texto grande» propio del sitio.

No se ha localizado en el `main` inspeccionado una implementación equivalente que haya que preservar o completar. Más importante: F.1 ya protege targets renderizados y F.2 está convirtiendo Resize Text 200% + Text Spacing en un contrato sitewide de navegador. Esa es la solución correcta al problema de accesibilidad que pretendía abordar la idea original.

Añadir un segundo sistema de escala tipográfica dentro de la web introduciría un estado visual adicional que tendría que combinarse con zoom, tamaño de texto del navegador/SO, breakpoints, impresión, reduced motion y todos los componentes existentes.

## 2. Por qué sigue rechazado

Un modo propio no sustituye a que la interfaz sobreviva a las preferencias reales del usuario. Además puede producir falsos verdes: una escala elegida por el sitio puede ser más cómoda que el escenario normativo de 200% y ocultar defectos de min-content, grid, sticky UI o wrapping.

El sitio debe responder correctamente a la ampliación hecha por el usuario, no pedirle que utilice un control particular de DavidPortoDiaz.com.

## 3. Contratos que sí son autoridad

- **F.1:** targets interactivos renderizados, con geometría y excepción de espaciado cuando proceda.
- **F.2:** Resize Text 200% + WCAG Text Spacing sitewide, con artifact y enforcement una vez cierre su baseline.
- **F.4:** foco visible/no oculto cuando la composición crece.
- CSS fluido existente (`rem`, `clamp()`, grids shrinkable y hardening de reflow) debe corregirse en sus owners cuando falle.

## 4. Trigger excepcional de reevaluación

Solo reabrir la idea de un modo de lectura/tamaño propio si aparece una necesidad de producto distinta de «cumplir Resize Text», respaldada por investigación con usuarios y que no pueda resolverse mediante capacidades nativas y CSS resiliente.

Incluso entonces tendría que tratarse como preferencia opcional, no como sustituto de WCAG ni como condición para que la página sea usable al 200%.

## 5. Guardrails

- No persistir una escala propietaria en localStorage como parche de accesibilidad.
- No reducir el escenario F.2 para acomodar un modo propio.
- No multiplicar tokens/breakpoints por estados `normal/grande` sin evidencia de producto.
- No presentar el control como requisito para personas con baja visión.

## 6. Estado final

`REJECT · NATIVE_RESIZE_PREFERRED · F1_F2_ARE_THE_CORRECT_CONTRACT · NO_CODE`

F.5 no queda pendiente de implementación. La inversión debe permanecer en resiliencia real ante preferencias nativas del usuario.