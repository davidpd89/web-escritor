# Pendiente G — Herramienta de informe: assets sin referenciar en `assets/`

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-g-orphan-assets`

> **Alcance de esta PR y solo esta.** Añade una única herramienta de
> diagnóstico (`scripts/check-orphan-assets.py`) + su test. **No borra
> ningún fichero, no modifica ninguna página, no se engancha a ningún
> workflow de CI.** Es deliberadamente así — ver "Decisión" más abajo.

---

## El hallazgo

`assets/` pesa 401,9 MB. Desglose por formato:

| Formato | Ficheros | Peso |
|---|---|---|
| `.png` | 179 | 333,3 MB |
| `.jpg` | 92 | 52,6 MB |
| `.webp` | 75 | 8,0 MB |
| `.avif` | 42 | 3,5 MB |

No existía ninguna herramienta que comprobara si un fichero de `assets/`
está realmente referenciado por algo. `scripts/check-local-assets.py` ya
existente comprueba la dirección contraria (que cada referencia del HTML
apunte a un fichero real), pero nunca al revés.

## La herramienta: `scripts/check-orphan-assets.py`

Construye un "haystack" con todo el contenido de texto rastreado por git
(`.html/.css/.js/.mjs/.json/.xml/.txt/.md`) y comprueba, para cada imagen
bajo `assets/`, si su nombre de fichero aparece en algún sitio como
substring literal. Un fichero solo se marca si su nombre no aparece **en
absoluto** en nada rastreado por git — deliberadamente generoso para evitar
falsos positivos sobre assets realmente usados.

```
python scripts/check-orphan-assets.py                     # informe completo
python scripts/check-orphan-assets.py --exclude-campaign-assets
python scripts/check-orphan-assets.py --delete             # uso manual, nunca en CI
```

Resultado real contra el repo, a fecha de esta PR:

```
Orphan asset check: 340 unreferenced file(s), 394.1 MB total.
```

Con `--exclude-campaign-assets` (que carga `CAMPAIGN_SOCIAL_ASSETS` desde
`scripts/build-public-dist.py` en vez de duplicar esa lista a mano):

```
Orphan asset check: 337 unreferenced file(s), 393.8 MB total.
```

## Decisión (confirmada con el autor, 22/08/2026): no borrar nada todavía

La primera versión de esta tarea incluía un modo `--delete` pensado para
ejecutarse aquí mismo. **El autor confirmó que no procede**: la web está en
mitad de un rediseño, y la inmensa mayoría de lo que este informe lista no
es basura — es:

1. **Piezas de campaña para redes** (`manecillas-social-*.webp`), ya
   documentadas como intencionalmente sin referenciar en
   `CAMPAIGN_SOCIAL_ASSETS` (`scripts/build-public-dist.py`): se suben a
   mano a redes sociales, nunca deben enlazarse desde ninguna página.
2. **Fotografía y arte pendiente de la fase de diseño** que aún no ha
   arrancado — se enlazará cuando esa fase llegue, no antes.

Por eso esta herramienta es **solo de informe**: no tiene `--check` que
bloquee CI, no se engancha a ningún workflow, y su docstring dice
explícitamente que no se debe ejecutar `--delete` sin que un humano revise
la lista antes. Queda lista para cuando se decida una pasada de limpieza
real, después del rediseño.

## Test

`tests/test-check-orphan-assets.py`: repo git de fixture aislado (no toca
el repo real) con un asset referenciado, uno huérfano y uno de
campaña — confirma que el asset referenciado nunca se marca, que el
huérfano siempre se marca, y que `--exclude-campaign-assets` solo oculta el
de campaña.

```
python tests/test-check-orphan-assets.py
  ok   orphan.png detectado por defecto
  ok   used.png NO se marca como huerfano
  ok   campaign.webp se marca por defecto (sin excluir)
  ok   campaign.webp desaparece con --exclude-campaign-assets
  ok   orphan.png sigue detectado con --exclude-campaign-assets

tests/test-check-orphan-assets: OK
```

## Reglas de la casa

1. No se toca `main`.
2. No se borra ningún asset real en esta PR.
3. No se engancha `check-orphan-assets.py` a ningún workflow de CI.

## Test plan

- [x] `python scripts/check-orphan-assets.py` ejecutado en verde contra el repo real, salida pegada arriba
- [x] `python tests/test-check-orphan-assets.py` en verde
- [x] Cero cambios en `assets/` o en cualquier página publicada
