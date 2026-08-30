# E.3 · Revalidación de producción — `fetchpriority` y LCP

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **CONDITIONAL · HOME_ALREADY_HAS_SELECTIVE_HINT · NO_SITEWIDE_POLICY · MEASURE_WATERFALL_FIRST · NO_CODE**.

## 1. Resultado

La idea no es deuda de implementación global. El proyecto ya usa el mecanismo de forma selectiva en Home; una nueva aplicación solo se justifica si una medición identifica una imagen LCP estable cuya prioridad/descubrimiento sea un contributor real.

## 2. Evidencia directa de `main`

`index.html` contiene:

```html
<link rel="preload" as="image"
  href="assets/david-porto-foto-portada-sinfondo.webp"
  fetchpriority="high" />
```

Esto demuestra que existe una aplicación deliberada de preload + prioridad alta. No demuestra que la misma decisión sea correcta para otras familias ni que la imagen siga siendo LCP en todos los viewports.

## 3. Guía vigente contrastada

web.dev mantiene `fetchpriority` como una **pista** de prioridad relativa. Puede ayudar especialmente a una imagen LCP; para imágenes LCP que se descubren mediante CSS, el preload puede ser necesario para descubrimiento temprano. La misma guía advierte implícitamente contra convertir la señal en una prioridad universal: el navegador ya asigna prioridades y el beneficio depende del cuello de botella real.

Referencia vigente consultada el 30/08/2026:
- https://web.dev/articles/fetch-priority

## 4. Gate de cualquier extensión

Antes de añadir `fetchpriority="high"` a otra superficie debe existir:

1. ruta y viewport representativos;
2. elemento LCP repetible en varias ejecuciones;
3. waterfall/trace que muestre `resource load delay` o prioridad insuficiente;
4. ausencia de `loading="lazy"` en el candidato;
5. ausencia de doble descarga por preload/src/srcset;
6. before/after que mejore LCP sin degradar CSS/font/otros recursos críticos.

Si el LCP es texto o el contributor es TTFB/render delay, E.3 no aplica.

## 5. No hacer

- `fetchpriority="high"` en todas las hero images;
- varias imágenes `high` por plantilla sin evidencia;
- combinar prioridad alta con lazy load del candidato LCP;
- añadir preload a una variante que el navegador no termina consumiendo;
- inferir el LCP por apariencia visual;
- usar una ejecución aislada de Lighthouse como autorización para rollout.

## 6. Estado para integración

No se modifica HTML en esta PR. E.3 queda como contrato medido y no como checklist de atributos. La aplicación existente de Home se preserva hasta que un análisis específico demuestre que debe cambiar.