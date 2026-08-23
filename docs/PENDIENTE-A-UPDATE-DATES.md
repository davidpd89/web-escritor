# Pendiente A — Retirar la doble autoridad sobre `sitemap.xml`

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-a-update-dates`

> **Alcance de esta PR y solo esta.** No toques nada fuera de
> `.github/workflows/`. Si ves otra cosa que arreglar de paso, anótala en la
> descripción de la PR en vez de tocarla aquí — hay otras PRs (B–F) cubriendo
> el resto y no deben pisarse.
>
> **No requiere claves ni acceso a Cloudflare/Brevo.** Es un cambio de
> workflow y verificación con Python puro.

---

## El problema

`.github/workflows/update-dates.yml` sigue en el repo. Ante cualquier HTML
cambiado, fuerza el `<lastmod>` del sitemap a la fecha del día y hace commit +
push automático a `main` con `contents: write`.

Eso tenía sentido cuando el sitemap se mantenía a mano. Ya no: existe
`scripts/build-sitemap.py`, que usa `dateModified` explícito del JSON-LD de
cada página como única fuente de verdad, y se verifica con `--check` dentro de
`.github/workflows/content-index-check.yml`.

Confirmado en HEAD:

```bash
$ ls .github/workflows/update-dates.yml
.github/workflows/update-dates.yml        # todavía existe

$ grep -n "build-sitemap.py" .github/workflows/content-index-check.yml
# ya está wireado ahí
```

Esto no es una opinión — está documentado como decisión ya tomada en al menos
6 sitios del dossier de propuestas (`WEB DAVID PORTO nuevas ideas/00_INDICE_Y_DECISIONES.md`
§"Decisión técnica 16/08", `01_AUDITORIA_ACTUAL.md` P2, `15_REGISTRO_DE_CORRECCIONES.md`
C-073, `16_IMPLEMENTACION_CODIGO_LISTA.md`, `18_AUDITORIA_REPOSITORIO_SEGUNDA_VUELTA.md`,
`27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md` §18). Nunca se llegó
a aplicar.

Hoy es inofensivo por accidente: el `sed` del workflow ya no encaja con el
formato de una sola línea que usa el `sitemap.xml` actual, así que no escribe
nada. Pero sigue armado — un cambio de formato del sitemap (por ejemplo, si se
reformatea con indentación) lo reactivaría sin que nadie lo note, con dos
sistemas escribiendo `lastmod` distinto para la misma URL, uno de ellos
haciendo push directo a `main` sin PR.

## Qué hacer

1. Eliminar `.github/workflows/update-dates.yml`.
2. Confirmar que `content-index-check.yml` sigue ejecutando
   `python scripts/build-sitemap.py --check` como parte del job (ya lo hace;
   no debería hacer falta tocar ese fichero).
3. Ejecutar en local:
   ```bash
   python scripts/build-sitemap.py --check
   ```
   Debe pasar sin cambios — el workflow retirado ya estaba inerte, así que el
   sitemap versionado no debería moverse por este cambio.
4. Revisar si algún otro fichero (README, docs de operación) menciona
   `update-dates.yml` como parte del flujo y actualizarlo si es así
   (`grep -rn "update-dates" --include="*.md" .`).

## Qué NO hacer

- No toques `scripts/build-sitemap.py` ni `content-index-check.yml` salvo que
  el paso 2 revele que de verdad falta el `--check` (no debería).
- No regeneres `sitemap.xml` "por si acaso" si el `--check` ya pasa limpio.

## Criterio de aceptación

- `.github/workflows/update-dates.yml` no existe.
- `python scripts/build-sitemap.py --check` pasa en local sin diferencias.
- La PR describe qué se comprobó (comando + resultado), no solo "borrado el
  fichero".

## Reglas de la casa

1. No se toca `main` ni se despliega nada.
2. No inventes un PASS: pega la salida real del comando `--check`.
3. Si al borrar el workflow aparece algo inesperado (por ejemplo, el
   `--check` falla porque el sitemap real llevaba tiempo desactualizado por
   otra razón), no lo arregles aquí — repórtalo en la descripción de la PR
   como hallazgo nuevo y déjalo para revisión, no lo fuerces a verde.
