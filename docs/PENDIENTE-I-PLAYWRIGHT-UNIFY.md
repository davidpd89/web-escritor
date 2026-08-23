# Pendiente I — Unificar versión de Playwright en CI + cachear el navegador

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Rama de esta tarea: `pendiente-i-playwright-unify`

> **Alcance de esta PR y solo esta.** Añade `package.json`/`package-lock.json`
> en la raíz y reescribe el paso "Install Playwright" (con distintos nombres)
> en los 21 workflows de `.github/workflows/` que lo tenían. No toca la
> lógica de ningún test, solo cómo se instalan sus dependencias de Node.

---

## El problema

El repo no tenía `package.json`. Cada uno de los **21 workflows de QA con
navegador** instalaba Playwright por su cuenta con
`npm install --no-save[--package-lock=false] playwright@X.Y.Z`, y las
versiones estaban partidas en dos sin que nadie lo hubiera notado:

| Versión | Workflows |
|---|---|
| `playwright@1.55.0` | 13 |
| `playwright@1.62.1` | 8 |

Distintos gates de CI corrían contra **motores Chromium distintos**. Un
cambio que rompe en 1.62.1 podía pasar limpio en 1.55.0, y viceversa —
inconsistencia real, no cosmética. Además, cada job **redescargaba** npm y
el binario de Chromium desde cero en cada ejecución, sin ninguna caché.

## La solución

1. **`package.json` en la raíz** (nuevo): fija `playwright@1.62.1`,
   `pa11y-ci@4.1.1` y `@lhci/cli@0.15.1` — las tres versiones que ya
   coincidían entre workflows salvo la de Playwright. Documentado en el
   propio fichero que este repo no tiene build step de Node: existe
   únicamente para fijar en un lockfile compartido las dependencias de
   CI/QA.
2. **`package-lock.json`** (nuevo, generado con `npm install`): la fuente
   real de verdad para `npm ci`.
3. **Los 21 workflows**: el paso ad-hoc de instalación se sustituye por:
   - `npm ci` (instala exactamente el lockfile, reproducible).
   - `actions/cache@v4` sobre `~/.cache/ms-playwright`, con clave
     `playwright-chromium-${{ hashFiles('package-lock.json') }}` — el
     binario de Chromium solo se descarga la primera vez; los siguientes
     runs con el mismo lockfile lo recuperan de caché.
   - `npx playwright install --with-deps chromium` solo si la caché falla;
     `npx playwright install-deps chromium` (solo dependencias del SO, sin
     redescargar el binario) si la caché acierta.
4. `samuel-ecosystem-browser-qa.yml` tenía además un `sudo apt-get install
   poppler-utils` mezclado en el mismo paso — se separó en su propio step,
   sin tocar su comportamiento.
5. Los `npm init -y` que algunos workflows necesitaban antes de instalar
   sin lockfile (`tools-events-memory-browser-qa.yml`,
   `samuel-ecosystem-browser-qa.yml`, `home-map-interaction-qa.yml`) ya no
   hacen falta: `package.json` existe en la raíz del repo.

## Verificación real (no solo lectura de YAML)

```
$ python -c "import yaml, glob; ..."
checked 29 files, 0 error(s)          # los 29 workflows siguen siendo YAML valido

$ npm ci
added 400 packages, and audited 401 packages in 18s   # exit 0

$ npx playwright --version
Version 1.62.1

$ node qa/home-map-interaction.mjs    # pipeline end-to-end real, Chromium real (via QA_CHROMIUM_EXECUTABLE_PATH en este entorno)
HOME MAP INTERACTION QA PASS

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs
```

`grep -RIn "npm install --no-save" .github/workflows/` → sin resultados:
los 21 workflows quedaron migrados, ninguno se saltó.

## Nota sobre `npm audit`

`npm ci` reporta 13 vulnerabilidades (2 low, 1 moderate, 10 high) en
dependencias transitivas de `pa11y-ci`/`@lhci/cli` (versiones antiguas de
`puppeteer`, `glob`, etc.) — **preexistentes**, no introducidas por esta
PR: son las mismas versiones (`pa11y-ci@4.1.1`, `@lhci/cli@0.15.1`) que ya
usaban los workflows antes de esta rama. Fuera de alcance aquí; se anota
para una PR futura de mantenimiento de dependencias.

## Reglas de la casa

1. No se toca `main`.
2. No se cambia la versión de `pa11y-ci` ni `@lhci/cli` (ya coincidían).
3. No se modifica la lógica de ningún test QA, solo su instalación.

## Test plan

- [x] Los 21 workflows migrados, verificado con grep que ninguno quedó con el patrón antiguo
- [x] YAML válido en los 29 workflows tras el cambio
- [x] `npm ci` reproducible en verde
- [x] `npx playwright --version` confirma 1.62.1 (versión única)
- [x] Al menos un QA de navegador ejecutado end-to-end contra el `node_modules/playwright` instalado por lockfile
