# N.3 · Glosario interno de nombres propios para traducción futura

Fecha de reconstrucción: 2026-08-29  
Fuente: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `DEFER`.

## Veredicto

Un glosario interno de traducción puede ser útil cuando exista un **workflow real de traducción/adaptación**, pero crear ahora una autoridad paralela de nombres propios añade mantenimiento sin un consumidor real.

## Hipótesis original

Documento interno —no público— con grafía canónica de nombres, lugares y términos del universo para evitar inconsistencias cuando llegue una traducción.

## Evolución

- revisión: prematuro sin proyecto de traducción;
- matriz: `CONDICIONAL`/diferir hasta workflow real;
- autoridad final: `DEFER`;
- revalidación independiente: N.1–N.3 mantenidas.

La evolución corrige la intuición de que “documentar antes siempre es mejor”: una taxonomía de traducción sin idioma objetivo, traductor, derechos ni decisiones terminológicas reales puede convertirse en una fuente obsoleta.

## Relación con B.9

B.9 ya gobierna el glosario **público/canónico del universo** para lectores. N.3 no debe duplicarlo.

Cuando exista traducción, el glosario N.3 debería referenciar la autoridad de canon y añadir solo información de localización, por ejemplo:

```text
canonical term
source work
source-language spelling
target-language decision
translate | transliterate | keep
approved form
context/notes
spoiler level
reviewer/date
```

## Relación con C.9/N.1/G.4

- C.9: proyecto/licencia real primero;
- N.1: hreflang solo después de URLs traducidas reales;
- G.4: no metadata inglesa artificial.

N.3 es una herramienta de producción de ese futuro proyecto, no una señal SEO ni una página pública.

## Qué términos podrían necesitarlo

Solo cuando haya proyecto real:

- personajes;
- topónimos;
- objetos mágicos;
- instituciones/facciones;
- sistemas de magia;
- títulos/cargos;
- expresiones recurrentes cuyo tratamiento deba ser consistente.

No incluir datos que no estén en canon aprobado.

## Fuente de verdad

El glosario de traducción nunca debe convertirse en autoridad primaria del lore. Las decisiones de canon siguen en las autoridades editoriales existentes; N.3 almacena decisiones lingüísticas derivadas.

## Derechos y confidencialidad

Si incorpora material de manuscrito no publicado:

- no hacerlo público;
- limitar acceso;
- no enviarlo a servicios externos automáticamente;
- aplicar las mismas reglas de privacidad/rights del proyecto.

## Trigger de reapertura

```text
real translation/adaptation project
AND target language selected
AND rights/licence clear
AND translator/editorial owner
AND canonical source material identified
```

## Qué NO hacer

- crear `/glosario-traduccion/` indexable;
- inventar traducciones con IA;
- traducir nombres antes de conocer idioma/contexto;
- duplicar B.9;
- usarlo como excusa para abrir `/en/`;
- publicar secretos/spoilers del manuscrito.

## Definition of Done futura

- una única autoridad de decisiones terminológicas;
- referencia explícita al canon;
- idioma objetivo definido;
- owner/revisor;
- versionado;
- historial de cambios;
- control de spoilers/confidencialidad;
- integración con QA de traducción, no con SEO automático.

## Revalidación actual

No existe un proyecto real de traducción pública que active esta necesidad. El estado `DEFER` continúa siendo correcto.

## Trazabilidad

- backlog original N.3;
- revisión 108/108;
- matriz;
- autoridad final `DEFER`;
- revalidación independiente;
- relaciones con B.9/C.9/N.1/G.4.

## Recomendación

No crear el glosario ahora. Cuando exista una traducción real, derivarlo del canon existente y limitarlo a decisiones lingüísticas que el equipo/traductor necesite de verdad.