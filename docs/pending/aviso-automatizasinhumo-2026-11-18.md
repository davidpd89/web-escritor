# Aviso desde automatizasinhumo (18/11/2026)

Hallazgos de automatizasinhumo-web que afectan o sirven a web-escritor. Solo información: configurarlo cuando se trabaje aquí.

## 1. Cola de Actions saturada (afecta a las dos)
- Los trabajos simultáneos de Actions son por cuenta: web-escritor tenía ~70 trabajos en cola y 10 en curso, y bloqueaba también la CI de automatizasinhumo.
- 80 de los 83 workflows con `pull_request` no tienen `concurrency` con `cancel-in-progress: true`; cada push a una PR deja corriendo y en cola las ejecuciones viejas. Lista: script de comprobación al final.
- Arreglo adoptado (sintaxis oficial de GitHub, sin código propio), en cada workflow de PR:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

  (En `main` no se cancela, para no cortar despliegues ni la carga.)

## 2. Empleados de seguridad que aquí faltan (repo público)
| Empleado | Licencia | Estado en web-escritor | En automatizasinhumo |
|---|---|---|---|
| zizmor (`zizmorcore/zizmor-action`) | MIT | 1 workflow | Workflow `vigilantes-cadena.yml` (PR #13). Encontró un workflow en Latin-1 que ninguna herramienta podía leer; aquí los 105 ficheros de `.github/` son UTF-8 (comprobado). |
| Dependency Review (`actions/dependency-review-action`) | MIT | No | Bloquea dependencias con vulnerabilidad alta o licencia no admitida. Requiere activar alertas de Dependabot: aquí `vulnerability-alerts` da 404 (desactivadas). |
| OpenSSF Scorecard (`ossf/scorecard-action`) | Apache-2.0 | No | Semanal, resultados en Code scanning. |
| Harden-Runner (`step-security/harden-runner` v2.23.0) | Apache-2.0 | No | Recomendación nº 1 de GPT: vigila la salida de red de los jobs con secretos (modo `audit`, gratis en repos públicos). |
| Socket Security (App) | Gratis 1 dev | No | Detecta paquetes maliciosos/typosquatting que Dependabot no ve. Instalación con 1 clic (decisión de David). |

Plantilla lista para copiar: `.github/workflows/vigilantes-cadena.yml` de davidpd89/automatizasinhumo-web.

## 3. Empleados SEO (ronda 10 de GPT en automatizasinhumo)
Útiles también aquí (catálogo grande): SiteOne Crawler (MIT, binario oficial, rastreo SEO con `--ci`), jdevalk/seo-graph (MIT, inspector JSON-LD), sitemap.js (MIT, sitemap + canonical), indexnow-action (MIT). Detalle: `manual/auditorias-gpt/ronda-10-respuesta.md` y tareas C12-C16 en `manual/equipo/copilot.md` de automatizasinhumo-web.

## Comprobación
```bash
git ls-files .github/workflows | xargs grep -L 'cancel-in-progress' | xargs grep -l pull_request
```
