# O.1 · Feed RSS generado, autodetectado y visible

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.

## Veredicto

O.1 empezó como una mejora UX de bajo coste —hacer visible un RSS que probablemente ya existía— y terminó correctamente como `ALREADY_COVERED`: el feed no solo existe, sino que tiene builder, `--check`, autodiscovery y enlace visible.

No crear un segundo feed, otra ruta RSS ni una plataforma de sindicación paralela.

## Hipótesis original

La idea inicial proponía:

> si `rss.xml`/similar ya existe, enlazarlo visiblemente desde Cuaderno, no solo en `<head>`.

El objetivo era ofrecer un canal abierto de distribución sin intermediario.

## Evolución histórica

### Revisión → `PARTIAL_AUDIT`

La primera revisión detectó que era necesario confirmar el feed real y su alcance antes de añadir nada.

### Matriz → `IMPLEMENTAR BAJO COSTE`

La matriz proponía:

> RSS visible y auto-discovery; comprobar copy/UX, no promoverlo más que newsletter.

### Autoridad final → `ALREADY_COVERED`

La inspección profunda cerró la idea:

> Feed ya se genera (`build-feed.py`) y existe autodiscovery. Un enlace visible es mejora UX opcional, no nueva infraestructura.

### Revalidación independiente

O.1–O.4 se mantuvieron sin correcciones.

## Revalidación actual de `main`

`main` confirma el estado cubierto.

### Builder

`scripts/build-feed.py`:

- genera `/cuaderno/feed.xml`;
- usa RSS 2.0;
- añade `xml-stylesheet` hacia `/assets/rss.xsl`;
- excluye `noindex`;
- excluye hubs `CollectionPage` para no duplicar artículos;
- limita a 50 entradas;
- ordena de forma determinista;
- ofrece `--check` para detectar feed desactualizado;
- valida XML/XSL.

### Autodiscovery

`/cuaderno/` publica:

```html
<link rel="alternate"
      type="application/rss+xml"
      title="Cuaderno del autor — David Porto Díaz"
      href="https://davidportodiaz.com/cuaderno/feed.xml" />
```

### Enlace visible

El footer actual incluye:

```text
RSS del Cuaderno → /cuaderno/feed.xml
```

Por tanto la propuesta original está materialmente cubierta.

## Contratos importantes del feed

- solo contenido que realmente sea entrada editorial;
- no hubs/colecciones duplicadas;
- no páginas `noindex`;
- URL/guid canónicos;
- output determinista;
- feed regenerado cuando cambia el corpus;
- XSL válido para lectura humana sin afectar lectores RSS.

## Relación con newsletter

RSS y newsletter son canales complementarios:

- RSS: abierto, pull, sin registro;
- newsletter: opt-in email, canal editorial/relacional.

No hay que esconder RSS para maximizar captación ni promocionarlo por encima del journey principal si no ayuda al usuario.

## Qué NO hacer

- crear `/rss.xml` además de `/cuaderno/feed.xml` sin necesidad;
- crear Atom paralelo por checklist;
- meter hubs temáticos como entradas nuevas;
- añadir tracking individual al feed;
- usar un SaaS de RSS para algo ya resuelto;
- convertir el feed en fuente de contenido diferente al Cuaderno;
- duplicar títulos/descripciones artificialmente para SEO.

## QA futuro

Si se toca O.1:

```bash
python scripts/build-feed.py --check
```

Además:

- `feed.xml` parsea;
- XSL existe y parsea;
- autodiscovery apunta al feed real;
- enlace visible no rompe navegación;
- entradas canónicas responden;
- no se incluyen `CollectionPage`/`noindex`.

## Trazabilidad

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `PARTIAL_AUDIT`;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR BAJO COSTE`;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — `ALREADY_COVERED`;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — mantenida;
- `scripts/build-feed.py` y `cuaderno/index.html` actuales — evidencia de implementación.

## Recomendación

**No implementar O.1 de nuevo.** Mantener el feed existente, su enlace visible y sus checks. Cualquier mejora futura debe extender esa autoridad.