# AB — Diseño final · Autor + Prensa + Eventos

Fuente de diseño: `22 — AUTOR + PRENSA + EVENTOS MASTER SPEC V1` de Drive.
Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Estado real

El repo ya tiene familia V1 específica (`v1-families.css` + `v1-identity.css`) y páginas públicas con shell V1, contenido factual, schema y media real. Esta PR no rehace hechos ni SEO: cierra la dirección de arte documental y su consistencia entre Autor, Prensa y Eventos.

## Owner

### Autor

- persona antes que currículum;
- retrato real como pieza editorial principal, sin marco/app-card;
- nombre + descriptor + obra como primer recorrido;
- bio en dos capas visuales sin esconder la capa larga SEO;
- trayectoria como columna/ledger cronológico, no timeline SaaS de bolitas;
- bibliografía visual desigual: Manecillas dominante, Samuel secundario, Jaula neutra;
- reconocimientos como ledger factual;
- contacto final silencioso y claro.

### Prensa

- cabecera funcional;
- press kit como archivo profesional de recursos reales;
- cobertura en lista/ledger fecha|medio|tipo|titular|acción;
- solo una aparición destacada rompe ritmo si existe motivo real;
- fotografías únicamente cuando pertenecen a la evidencia/cobertura.

### Eventos

- próximos primero, pasado después;
- fecha como ancla tipográfica;
- filas/episodios editoriales, no cards de agenda;
- evento destacado solo con datos reales;
- sin countdown, ticket falso, confeti ni cartel inventado;
- archivo por año solo cuando ayude.

## Deltas a cerrar

1. Autor hero: validar composición 320/390/768/1024/1440/1728 con crop real y CTA en primer recorrido razonable.
2. Trayectoria: máximo 5–7 hitos simultáneos destacados; resto como archivo sobrio.
3. Prensa: reforzar escaneabilidad y jerarquía sin thumbnails obligatorios.
4. Eventos: estados próximo/vacío/pasado deben ser comprensibles sin depender del color.
5. Media kit: formato/purpose de cada recurso visible, sin iconografía de descarga sobredimensionada.
6. Continuidad Home→Autor por retrato se coordina con #82; AB prepara el destino.
7. Toda media consume procedencia de #83.
8. Si no existe próximo evento, diseñar el empty state factual sin inventar actividad.
9. Mantener HTML/schema/fechas/lugares sincronizados y visibles.

## Coordinación

- #82 posee View Transition Home→Autor.
- #83 posee procedencia/media/color.
- #57 posee fechas/SEO editorial.
- #77 posee infraestructura/calendarios y gate de eventos futuros reales.
- #66 posee evidencia/compatibilidad cross-engine.
- #78 posee QA mobile/resiliencia.
- #84 certifica identidad final.
- #68 conserva navegación global: Prensa/Eventos siguen dentro del territorio acordado.

## No hacer

- no inventar eventos, fotos, dossiers, medios, premios o testimonios;
- no timeline de producto ni zigzag móvil;
- no cards repetidas de prensa/eventos;
- no badges/trofeos 3D;
- no parallax del retrato ni contadores animados;
- no rasterizar fechas, medios o datos públicos.

## Definition of Done

- Autor se siente humano/editorial, no corporativo;
- Prensa se escanea rápido y mantiene archivo profesional;
- próximos eventos se encuentran inmediatamente cuando existan;
- ausencia de evento futuro tiene estado diseñado y factual;
- móvil conserva identidad sin offsets peligrosos;
- teclado/focus/reduced-motion/200% zoom correctos;
- datos/schema/URLs preservados;
- #84 puede reconocer la misma identidad sin logo entre Home, Autor, Prensa y Eventos.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.