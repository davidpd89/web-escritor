# AC — Diseño final · Herramientas

Fuente de diseño: `23 — HERRAMIENTAS MASTER SPEC V1` de Drive.
Base auditada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

## Hallazgo real

Aquí sí existe una contradicción directa entre autoridad de diseño y repo actual.

El HTML generado de `/herramientas/` documenta literalmente que el hub usa una **card grid** de `v1-families.css`. El master 23 ordena justo lo contrario: instrumentos editoriales, jerarquía desigual, filas/placas y no 3/4 cards idénticas con icono+título+descripción+botón.

No es un problema funcional: es una deuda clara de presentación final.

## Owner

### Hub de Herramientas

- H1 + explicación breve, no dashboard;
- una herramienta prioritaria puede dominar 6–7 columnas si existe motivo real;
- resto como filas/placas editoriales de escala variable;
- cada unidad explica problema que resuelve + nombre + frase + enlace;
- icono solo si identifica de verdad;
- taxonomía/filtros solo si ayudan al corpus real;
- mobile vertical y totalmente navegable con un toque.

### Página de herramienta

- contenido/H1 antes de la interfaz;
- input y resultado como protagonistas;
- formularios nativos, labels visibles, help/error asociados;
- resultado legible/copIABLE/editable;
- estados empty/loading/success/error reales;
- loading solo si existe espera real;
- una acción primaria por estado;
- diseño editorial, no panel SaaS ni terminal/laboratorio.

## Contrato visual

- Paper/Ink y hairlines del sistema;
- acento frío únicamente si procede del sistema/token aprobado;
- “instrumento” como unidad propia: índice opcional + nombre grande + descripción + estado factual + enlace;
- hover/focus contenido: contraste de línea y desplazamiento 0–2px como máximo;
- sin sombras-card, levitación, score ornamental, partículas, blueprint global ni estética IA-tech.

## Deltas concretos

1. Sustituir la gramática actual de `.id-cards/.id-card` del hub por composición editorial sin perder enlaces/datos/builder.
2. Mantener `data/tools-hub.json` como autoridad de contenido; el cambio visual no crea un hub manual paralelo.
3. Preservar filtros actuales solo si siguen siendo útiles y accesibles; rediseñar su apariencia para que no parezcan pills/dashboard.
4. Elegir una herramienta piloto representativa antes de extender visualmente todas: textarea/input + varios controles + validación + resultado + copiar + error.
5. Verificar 320/390 con teclado virtual abierto y resultados/textos extremos.
6. Mantener procesamiento local y CSP/privacidad de herramientas que ya lo requieren.
7. No enviar texto introducido por usuarios a analítica.
8. El resultado debe seguir siendo comprensible sin motion.

## Coordinación

- #59/#72/#73/#80 y otras PR funcionales siguen siendo owners de motores/rutas/herramientas nuevas; AC no reimplementa lógica.
- #61 conserva runtime/scoping.
- #63 conserva taxonomía analítica segura.
- #65 conserva Playwright/CI.
- #66 conserva cross-engine.
- #78 conserva QA mobile/resiliencia.
- #83 posee color/procedencia cuando exista media.
- #84 certifica identidad/craft final.
- #68 conserva navegación global.

## No hacer

- no cambiar fórmulas/motores para cuadrar diseño;
- no inventar categorías/estados beta/nuevo;
- no wizard multistep sin necesidad;
- no spinner para cálculo inmediato;
- no sticky CTA sobre teclado;
- no ocultar SEO útil en tabs JS por limpieza visual;
- no crear cards redondeadas de nuevo bajo otro nombre.

## Definition of Done

- `/herramientas/` deja de parecer un catálogo SaaS/card grid y se reconoce como territorio editorial propio;
- builder y `data/tools-hub.json` siguen siendo autoridad;
- una herramienta piloto demuestra el patrón antes del rollout total;
- estados y errores son utilizables con teclado/lector de pantalla;
- 320/390/768/1024/1440/1728 y 200% zoom sin pérdida;
- privacidad/local-only intactos;
- resultado y formularios no dependen de motion;
- #84 puede reconocer la misma marca sin confundir Herramientas con Libro o Cuaderno.

PR DRAFT. No tocar `main`, no deploy, no auto-merge.