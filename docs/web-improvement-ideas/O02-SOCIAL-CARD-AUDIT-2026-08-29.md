# O.2 · Tarjetas sociales específicas: auditoría antes que generación masiva

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `PARTIAL_AUDIT`.

## Veredicto

La idea original proponía una OG image única por artículo. #135 la refinó: **antes de construir un pipeline masivo hay que inventariar qué URLs siguen usando una tarjeta genérica y priorizar solo libros/artículos con señal real**.

`main` ya contiene un auditor específico, `scripts/check-social-cards.py`, que cubre exactamente esa primera capa. Por tanto O.2 no es «crear otro checker» ni «generar una imagen por URL».

## Hipótesis original

> tarjeta social pre-generada por artículo: título + marca, en vez de una única imagen genérica repetida.

Valor esperado: mayor coherencia/CTR/compartibilidad.

## Evolución

### Revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

La primera revisión consideró razonable un pipeline determinista para piezas prioritarias, evitando generación IA genérica.

### Matriz → `PILOTAR ALTO`

La matriz propuso OG específica en artículos/libros clave, mediante plantilla determinista.

### Autoridad final → `PARTIAL_AUDIT`

El cierre fue más prudente:

> inventariar qué URLs comparten OG genérica; priorizar libros/artículos con señales reales antes de pipeline masivo.

### Revalidación independiente

O.1–O.4 se mantuvieron.

## Revalidación actual de `main`

`scripts/check-social-cards.py` ya:

- audita HTML indexable;
- exige metadata OG/Twitter mínima;
- comprueba canonical = `og:url`;
- valida que assets locales existan;
- comprueba dimensiones declaradas vs fichero;
- avisa si una card supera 1 MB;
- identifica artículos que aún usan `DEFAULT_ARTICLE_CARD`;
- genera inventario de reutilización;
- soporta adopción report-only y modo `--strict` posterior.

Eso cubre la fase de inventario que #135 exigía.

## Qué queda por decidir

Para cada URL marcada con card genérica:

1. ¿recibe tráfico/shares o tiene valor estratégico?
2. ¿dispone de una imagen editorial real mejor?
3. ¿una card específica mejoraría comprensión al compartir?
4. ¿se puede generar determinísticamente sin arte IA genérico?
5. ¿el coste de mantenerla compensa?

Resultado por URL:

```text
KEEP_GENERIC
USE_EXISTING_EDITORIAL_IMAGE
GENERATE_TEMPLATE_CARD
NO_ACTION
```

## Reglas de diseño

Si se genera una card:

- plantilla humana/determinista;
- título legible;
- marca discreta;
- dimensiones consistentes;
- asset optimizado;
- `og:image:alt` contextual;
- no meter texto excesivo;
- no sustituir una imagen editorial fuerte por title-on-gradient por cumplir checklist.

## Relación con A.11/R.72

La investigación de media de #135 ya fijó que relevancia semántica de imagen importa más que «tener una imagen distinta». `primaryImageOfPage`, Book `image` y `og:image` deben describir realmente la página.

## Qué NO hacer

- generar automáticamente una imagen para cada URL;
- IA decorativa genérica;
- duplicar `check-social-cards.py`;
- hard fail inmediato por toda card genérica heredada;
- elegir cards por estética sin señal de uso;
- alterar canonical/social metadata sin QA;
- crear assets de varios MB.

## Definition of Done futura

- inventario actual de cards genéricas;
- priorización por familia/señal;
- plantilla definida solo si hay volumen suficiente;
- output determinista;
- checker valida existencia/dimensiones/alt;
- no duplicación de imagen authority;
- social debugger/manual smoke para páginas clave.

## Trazabilidad

- backlog original O.2;
- revisión `IMPLEMENT_AFTER_CURRENT_DEBT`;
- matriz `PILOTAR ALTO`;
- autoridad final `PARTIAL_AUDIT`;
- revalidación independiente;
- `scripts/check-social-cards.py` actual.

## Recomendación

Usar el auditor existente para producir el inventario real y decidir asset por asset. No construir un pipeline masivo hasta que los hallazgos demuestren que compensa.