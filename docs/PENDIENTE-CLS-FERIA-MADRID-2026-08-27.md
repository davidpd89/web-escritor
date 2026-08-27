# Pendiente — CLS sin resolver en /cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/

Fecha: 2026-08-27

## Qué pasa

El check "Cuaderno Lighthouse" (browser-qa) falla de forma determinista en CI
(Linux) con `cumulative-layout-shift` ≈ 0.177 (presupuesto 0.1) solo en esta
página. Se mergeó la PR #108 igualmente porque las otras 38 comprobaciones
pasan, es un problema de rendimiento/UX (no de seguridad/corrección), y el
resto del trabajo de esa PR (fix de los botones de email, etc.) ya estaba
verificado y era valioso desplegar.

## Lo que ya se probó

- La causa raíz original identificada esta sesión (`local('Georgia')` no
  resuelve en el runner Linux de CI, rompiendo el fallback métricamente
  ajustado de Newsreader/Instrument Serif) se corrigió encadenando Liberation
  Serif/DejaVu Serif en `assets/v1-fonts.css`. Eso arregló el mismo tipo de
  regresión en `/cuaderno/que-es-el-portal-fantasy/` (confirmado en CI,
  verde), pero en esta página el valor de CLS apenas cambió
  (0.17668 → 0.17731), así que no es la causa dominante aquí.
- No se pudo reproducir localmente (Windows, con Georgia instalado) ni con
  emulación móvil + CPU throttling 4x + red lenta vía CDP — solo se repite
  el shift menor y compartido del header (~0.03-0.05), no el de 0.177.
- Diferencia con las páginas que sí pasan: esta es la única página de
  artículo con una `figure.article-hero-figure` (imagen eager, 1500×2000,
  con `max-height:34rem` + `object-fit:cover`) y una `.article-gallery` de 4
  imágenes lazy adicionales (`assets/v1-editorial.css:122-137`). Revisado el
  CSS de ambas: usan `width:100%;height:auto` sobre atributos width/height
  reales, que debería reservar la caja sin depender de la carga real de la
  imagen — no se encontró una causa CSS obvia por lectura estática.

## Próximo paso sugerido

Reproducir en un entorno Linux real (o WSL) con las mismas condiciones que
`.github/workflows/cuaderno-browser-qa.yml` (lhci por defecto, mobile,
CPU throttling simulado) para poder inspeccionar el trace de Lighthouse
directamente y ver qué nodo/elemento reporta el shift. Sin eso, seguir
adivinando por lectura estática de CSS tiene rendimiento decreciente.
