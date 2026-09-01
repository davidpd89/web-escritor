# N.1 · `hreflang` solo con traducciones reales equivalentes

Fecha de reconstrucción: 2026-08-29  
Fuente: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `DEFER`.

## Veredicto

#135 rechazó preparar `hreflang` como infraestructura anticipada. Debe aparecer únicamente cuando existan **URLs reales, públicas y sustancialmente equivalentes en otro idioma**, con reciprocidad y canonicals coherentes.

## Hipótesis original

Preparar estructura de `hreflang`/rutas con antelación si se planea contenido en otro idioma, para no añadirlo después como parche.

## Evolución

- revisión: `DEFER` hasta existir contenido real equivalente;
- matriz: `DEFERIR`;
- autoridad final: `DEFER`;
- R.77 posterior: `DEFER_UNTIL_REAL_TRANSLATIONS`;
- revalidación independiente: N.1–N.3 mantenidas.

## Corrección conceptual

Diseñar una arquitectura futura no exige publicar señales falsas hoy. `hreflang` describe una relación existente; no una intención editorial.

No hacer:

- `hreflang="en"` hacia una URL española;
- placeholders indexables «English coming soon»;
- metadata inglesa sin contenido inglés;
- relaciones no recíprocas;
- traducciones automáticas thin solo para completar alternates;
- canonicals cruzados que contradigan el idioma de la página.

## Trigger

Reabrir únicamente cuando existan:

```text
language/locale approved
+ rights/project real
+ translated URLs publicables
+ semantic equivalence defined
+ reciprocal hreflang
+ canonical strategy
+ human QA
```

## Relación con C.9 y G.4

C.9 dejó traducción/adaptación en `DEFER` hasta proyecto/licencia real. G.4 rechazó metadata inglesa asistida por IA sin contenido internacional real. N.1 debe respetar ambas decisiones; ninguna PR futura puede usar `hreflang` para eludirlas.

## `x-default`

No añadir `x-default` por reflejo. Solo tiene sentido si existe una URL selector/default adecuada dentro de una arquitectura internacional real.

## QA futuro

- cada alternate responde 200;
- páginas equivalentes se referencian mutuamente;
- códigos de idioma/región válidos;
- canonical no contradice hreflang;
- sitemap/HTML usan la misma relación si se emplean ambos;
- no mezcla páginas no equivalentes;
- ninguna versión queda noindex accidentalmente.

## Revalidación actual

El sitio actual permanece esencialmente en español (`lang="es"`, `og:locale=es_ES`). No hay evidencia de una familia pública equivalente en otro idioma. Por tanto el `DEFER` sigue correcto.

## Trazabilidad

- backlog original N.1;
- revisión 108/108;
- matriz `DEFERIR`;
- R.77;
- autoridad final `DEFER`;
- revalidación independiente;
- relación con C.9/G.4.

## Recomendación

No implementar ahora. Definir `hreflang` como parte del proyecto de internacionalización real cuando ese proyecto exista, no como una señal preventiva.