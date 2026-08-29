# C.9 · Notas de traducción/adaptación / captación internacional temprana

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `DEFER`.

## Veredicto

#135 dejó C.9 diferida porque no existía un proyecto real de traducción/adaptación que justificase crear página, formulario o promesa internacional. Publicar una intención hipotética crea expectativa, mantenimiento y riesgo de metadata/hreflang incoherentes.

Reabrir solo con idioma, derechos/licencia, contenido traducido real y calendario/proyecto verificables.

## Hipótesis original

Crear una página de intención/registro de interés temprano si existían planes de traducción, para captar audiencia internacional antes de publicación.

## Evolución histórica

### Primera revisión → `DEFER`

La revisión concluye:

- sin plan real crea expectativa;
- añade mantenimiento;
- reabrir con idioma, derechos y calendario reales.

### Matriz → `DEFERIR`

> «Página de traducción solo cuando exista intención/licencia/proyecto real; no captar leads sobre producto hipotético.»

### Autoridad final → `DEFER`

> «Traducción/adaptación solo cuando exista proyecto/licencia real. No captar demanda sobre producto hipotético.»

### Revalidación independiente

La revalidación mantiene C.9 y todo el bloque de internacionalización diferido hasta existir contenido real equivalente.

## R.77 — corrección posterior sobre hreflang

La decimocuarta pasada añadió una regla explícita relevante:

`hreflang` = `DEFER_UNTIL_REAL_TRANSLATIONS`.

Solo debe usarse con URLs equivalentes realmente traducidas y relaciones recíprocas. Por tanto C.9 no autoriza:

- `hreflang="en"` sin página inglesa real;
- metadata inglesa sobre contenido español;
- canonicals cruzados artificiales;
- páginas placeholder «English version coming soon» indexables.

## Relación con G.4 / N.1–N.3

La investigación de #135 fue consistente:

- G.4 rechazó metadata inglesa sin páginas inglesas;
- internacionalización N.1–N.3 permanece diferida;
- C.9 no debe abrir una vía lateral que contradiga esas decisiones.

## Trigger de reapertura

Se necesitan hechos concretos:

```text
language selected
AND rights/licence verified
AND translation/adaptation project approved
AND real translated content or committed production schedule
AND owner/editorial review
AND canonical/hreflang architecture defined
```

Según el caso también:

- ISBN/edición específica;
- editorial/territorio;
- translator credit;
- rights holder;
- retailer/distribution info solo cuando exista.

## ¿Registro de interés?

Solo si existe un producto/proyecto suficientemente real para que el usuario entienda qué está esperando.

Debe explicarse:

- idioma/edición prevista;
- qué significa registrarse;
- qué comunicaciones recibirá;
- privacidad/consentimiento;
- posibilidad de baja;
- ninguna fecha inventada.

No crear otra lista Brevo/segmento sin necesidad y sin respetar la arquitectura H/email.

## Qué hacer antes de cualquier landing

1. documentar derechos;
2. confirmar alcance de traducción;
3. definir qué URLs serán equivalentes;
4. decidir si se traduce toda la experiencia necesaria o solo una ficha;
5. preparar copy real y revisión humana;
6. definir canonical/hreflang;
7. después decidir si hace falta captación previa.

## Riesgo de expectativa falsa

Una página pública puede hacer creer que:

- existe traducción contratada;
- hay fecha de lanzamiento;
- habrá edición internacional;
- se venderá en cierto país;
- una editorial concreta participa.

Nada de eso debe inferirse antes de estar confirmado.

## SEO/internacionalización

No usar:

- traducción automática masiva para fabricar cobertura;
- subdirectorios `/en/` vacíos;
- hreflang sin reciprocidad;
- meta descriptions inglesas en páginas españolas;
- auto-redirect por idioma;
- duplicados parcialmente traducidos;
- keyword pages por país.

Si llega el proyecto, las versiones deben ser útiles y sustancialmente equivalentes donde corresponda.

## Structured data

Idioma, edición, autoría/traducción/editorial deben reflejar hechos reales. No crear Book editions o offers antes de tenerlos.

## Relación con C.1

Un calendario de lanzamiento español de Manecillas no implica calendario internacional. C.9 requiere proyecto independiente.

## Relación con H/email

La captación de interés sería un journey de email sujeto a consentimiento/segmentación y evidencia E2E. C.9 no crea por sí sola ese sistema.

## Qué NO hacer

- página «English edition» hipotética;
- formulario «avísame» sin producto definido;
- traducir metadata solamente;
- hreflang anticipado;
- afirmar derechos internacionales no confirmados;
- crear perfiles/retailers internacionales inexistentes;
- traducción automática de toda la web por SEO;
- prometer fechas.

## Pasadas posteriores revisadas

Cuarta–decimotercera: sin cambio específico de C.9.  
Decimocuarta: R.77 refuerza `DEFER_UNTIL_REAL_TRANSLATIONS`.  
Decimoquinta: sin override.  
Revalidación independiente reafirma internacionalización diferida.

## Trazabilidad

- hipótesis original;
- revisión `DEFER`;
- matriz `DEFERIR`;
- overrides de internacionalización;
- R.77 hreflang;
- autoridad final `DEFER`;
- revalidación independiente.

## Definition of Done de esta reconstrucción

- [x] idea original preservada;
- [x] motivo de defer preservado;
- [x] trigger de derechos/idioma/proyecto documentado;
- [x] prohibición de captar leads de producto hipotético;
- [x] R.77 hreflang incorporado;
- [x] relación con G.4/N.* y H email separada;
- [x] sin implementación prematura.

## Recomendación para Clara/Claude

**No implementar ahora.** Reabrir C.9 únicamente cuando exista un proyecto de traducción/adaptación real y documentado. En ese momento diseñar internacionalización, derechos y captación como un único sistema coherente.