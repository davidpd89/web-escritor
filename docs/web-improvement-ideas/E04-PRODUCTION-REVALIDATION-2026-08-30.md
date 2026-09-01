# E.4 · Revalidación de producción — precarga de fuentes

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **CONDITIONAL · HISTORICAL_FONT_INVENTORY_STALE · OPTIONAL_IS_PRIMARY_POLICY · YELLOWTAIL_IS_EXPLICIT_EXCEPTION · NO_EXTRA_PRELOAD_WITHOUT_WATERFALL · NO_CODE**.

## 1. Corrección factual de la reconstrucción histórica

La reconstrucción del 29/08 contiene una afirmación que ya no describe `main`: no es cierto que todas las faces actuales usen `font-display: swap`, ni que el inventario vigente sea Marcellus/Inter/Merriweather/Yellowtail.

`assets/v1-fonts.css` actual declara, entre otras, estas familias del sistema V1:

- Instrument Serif normal/italic: `font-display: optional`;
- Manrope variable 400–700: `font-display: optional`;
- Newsreader normal/italic: `font-display: optional`;
- Allura: `font-display: optional`;
- Yellowtail 400: `font-display: swap`.

También existen fallbacks metric-matched para reducir reflow/CLS. Los comentarios de la propia autoridad explican que Yellowtail cambió de `optional` a `swap` para corregir un bug real donde, en recargas frías, el navegador podía quedarse toda la visita con la fallback pese a terminar de descargar la fuente.

La reconstrucción histórica se conserva como arqueología; este documento es la autoridad de producción.

## 2. Evidencia directa de Home

`index.html` precarga únicamente:

```html
<link rel="preload" as="font" type="font/woff2"
  href="assets/fonts/yellowtail-normal-400-latin.woff2" crossorigin />
```

No existe una razón de producción observada para convertir Instrument Serif, Manrope, Newsreader o Allura en nuevos preloads globales.

## 3. Guía vigente contrastada

web.dev sigue recomendando cautela con `preload` de fuentes: adelantar la descarga consume recursos que podrían necesitar CSS, imagen LCP u otros assets; además el preload puede ignorar decisiones como `unicode-range`. La recomendación es reservarlo a las fuentes más importantes y realmente necesarias pronto.

Referencia consultada el 30/08/2026:
- https://web.dev/articles/font-best-practices

## 4. Interpretación correcta del sistema actual

La combinación actual no es inconsistencia accidental:

- `optional` en las familias editoriales reduce swaps/reflow y permite fallback en condiciones adversas;
- fallbacks con métricas ajustadas reducen diferencias de layout;
- Yellowtail es una excepción deliberada porque el requisito visual de Home exige que termine mostrándose en esa visita;
- el preload de Yellowtail compensa su descubrimiento tardío y ese requisito de identidad.

Por tanto E.4 no debe homogeneizar todas las familias a `swap` ni añadir preloads para alcanzar una falsa consistencia.

## 5. Gate de una nueva precarga

Añadir otra fuente a preload solo si se demuestra:

1. uso real en el primer viewport de la familia;
2. descubrimiento tardío que afecta paint/LCP;
3. reutilización efectiva del preload, sin descarga duplicada;
4. mejora before/after;
5. ausencia de degradación de imagen LCP/CSS;
6. CLS/reflow sin regresión.

## 6. No hacer

- precargar todas las faces declaradas;
- cambiar `optional` a `swap` en bloque;
- asumir que toda fuente de marca es crítica;
- eliminar fallbacks metric-matched para simplificar CSS;
- usar warnings de preload como algo que se silencia sin diagnosticar;
- copiar a interiores el preload de Yellowtail sin que usen Yellowtail above-the-fold.

## 7. Estado para integración

No se cambia runtime. La corrección necesaria era documental: el owner actual ya contiene una estrategia más sofisticada que la descrita en la reconstrucción histórica. E.4 sigue condicional y medido.