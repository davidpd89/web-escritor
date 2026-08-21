# Asistente web — widget global

La superficie principal del asistente ya no debe depender de que el visitante descubra `/asistente/`. La experiencia global sigue el patrón de los chat launchers de productos maduros: una burbuja fija en la esquina inferior derecha abre un panel no modal y conserva una vía a página completa.

## Comportamiento canónico

- El launcher se carga de forma diferida desde `assets/v1-shell.js`; no bloquea el render crítico.
- Entra abierto automáticamente **una sola vez por sesión**, tras una espera corta y solo cuando la pestaña está visible y no hay otro `<dialog>` abierto.
- La apertura automática nunca mueve el foco. Una apertura iniciada por clic sí enfoca el campo de pregunta.
- Minimizar devuelve el foco al launcher. El launcher permanece visible para reabrir.
- `Escape` minimiza. Desde dentro del iframe, el cierre viaja por `postMessage` y el padre comprueba simultáneamente `origin` y `source`.
- Al abrir `Explorar`, el widget se minimiza para evitar dos capas competidoras. La nueva fila «Asistente» dentro de Explorar abre el widget con JavaScript y conserva `/asistente/` como fallback sin JavaScript.
- La ventana usa `/asistente/embed.html`, same-origin y `noindex,nofollow`, para reutilizar `assets/assistant.js`, Turnstile, cuotas, fallback local y validaciones sin duplicar lógica sensible.
- `/asistente/` y `/asistente/embed.html` nunca montan otra burbuja dentro de sí mismos.
- No hay sonido, falso estado «en línea», badge de mensajes sin leer, animaciones invasivas ni captura automática del foco.

## Responsive y accesibilidad

- Escritorio: panel máximo aproximado de 410 × 650 px sobre launcher circular de 60 px.
- Móvil: panel tipo bottom-sheet con `76dvh`, márgenes laterales y `safe-area-inset-*`.
- Panel `role=dialog` no modal, launcher con `aria-controls` + `aria-expanded` y botones con nombres accesibles.
- `prefers-reduced-motion` elimina animación/transición decorativa.
- El widget desaparece en impresión.
- La ventana completa sigue disponible desde el icono de «abrir en página completa» y desde el enlace interior del embed.

## Contexto de página sin ampliar datos personales

El iframe recibe únicamente el `pathname` de la página actual, limitado a 500 caracteres (nunca la query string), para adaptar las tres preguntas sugeridas. No recibe DOM, formularios, emails, texto seleccionado ni contenido escrito por el usuario en otras superficies. Los starters contextuales son deterministas y se generan localmente.

## Referencias de producto

- Cloudflare `ai-search-snippet` ofrece un `ChatBubbleSnippet` como superficie oficial flotante. Esta implementación copia el patrón de interacción, pero mantiene el Worker same-origin y el contrato de seguridad propio.
- Papercups popularizó el patrón launcher + iframe para aislar el widget del CSS anfitrión. Aquí el iframe es además same-origin y reutiliza exactamente el cliente auditado del asistente.

## Gate adicional antes de producción

Además del gate principal del asistente:

1. `node tests/test-assistant-widget.mjs` verde.
2. `python tests/test-assistant-widget-static.py` verde.
3. Comprobar auto-open solo una vez por sesión en desktop y móvil.
4. Confirmar que auto-open no cambia `document.activeElement`.
5. Confirmar minimizar/reabrir, `Escape`, enlace de Explorar y página completa.
6. Confirmar que abrir Explorar minimiza el widget y que cerrar Explorar no lo reabre por sí solo.
7. Probar iframe con Turnstile real en staging; extensiones que bloqueen Turnstile deben degradar a resultados locales.
8. Probar 320, 390, 768 y 1440 px, zoom 200 %, teclado y lector de pantalla.
9. Probar que `/asistente/` y `/asistente/embed.html` no contienen widget anidado.
10. Mantener el widget aunque la IA remota esté desactivada: debe seguir ofreciendo búsqueda/fallback local.

## Activación editorial y SEO

El widget puede fusionarse mientras `/asistente/` continúe `noindex` y la IA remota siga apagada. La integración canónica en `data/content-registry.json`, `data/navigation.json`, sitemap y footer se mantiene como gate de activación final, porque esas fuentes deben cambiar en el mismo commit que retire `noindex` y confirme la disponibilidad real del Worker. La fila de `Explorar` que añade el shell es una mejora progresiva y siempre conserva un enlace real a `/asistente/` si JavaScript no intercepta el clic.
