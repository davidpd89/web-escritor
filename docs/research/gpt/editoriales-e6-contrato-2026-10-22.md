> Archivo de investigación anterior a la reducción de alcance de #692. Las afirmaciones de pruebas pendientes y las referencias a módulos retirados son históricas. Véase [estado comprobado y uso actual](editoriales.md).

# E6.1–E6.2 · Contrato entre módulos y aprobación por campo

**Investigación GPT #692 · 22/10/2026 · DRAFT / NO MERGEAR.** Ningún código de este bloque se ha ejecutado. Fuentes: GitHub repo `davidpd89/web-escritor`, commit exacto `72ab6be7b8fee47dc82f29a7daf1373178e61ad1`; fichero de auditoría en [`editoriales-e6-baseline-2026-10-22.json`](editoriales-e6-baseline-2026-10-22.json).

## E6.1 — auditoría de contratos frente a `main`

**Confirmado directamente por lectura de JSON del mismo commit**, no por ejecutar pruebas: 150 editoriales, 11 sellos bibliográficos y 55 libros; 35 enlazan a `editorial_slug`, 20 a `editorial_catalogo_slug`, cero libros sin enlace y cero con ambos. Las 150 fichas conservan al menos una fuente primaria en el JSON; estados actuales: 72 `open`, 45 `closed`, 26 `unknown`, 7 `indirect`. No deducir cambios actuales en manuscritos de ninguna de estas cifras.

**E4 compatible por estructura:** 18 observaciones de fuente y 13 entidades con lista aprobada de hosts; las 18 URL coinciden literalmente con las listas de hosts revisados, en la inspección estática. **4 observaciones** (Bruguera, Montena, Beascoa y Debate) corresponden a sellos bibliográficos que **no existen en `data/editoriales.json`**: deben conservarse como `publisher_imprint` y **no** convertirse en estado del directorio. No hay URLs/fechas/resúmenes inválidos en ese cotejo estático. El conciliador E3 y el planificador E5 pueden consumir esas formas, pero **no se han importado/ejecutado juntos**, así que no afirmar que el pipeline esté probado.

**E5 caducidad propuesta**: con umbral 45 días para estado conocido y 90 días para `unknown`, 24 fichas de las 150 entrarían en la cola de reverificación a fecha 22/10/2026. Eso es una **regla experimental**, no prueba de información incorrecta y **nunca** causa cierre automático.

**Riesgo detectado:** las salidas E3/E4/E5 tienen fecha `as_of`, pero no incorporan autenticación ni una firma del commit de `main`. Es posible combinar informes generados el mismo día sobre distintos contenidos sin que E5 lo detecte. E6 añade huellas SHA-256 del JSON canónico de directorio + evidencia E4 + plan E5 para los **intentos de cambio**; aun así, el `main_sha` que introduce una persona en el manifiesto es **declarado y NO autenticado** por el script offline. La PR futura debe consultar el head real de GitHub y bloquear cambios si difiere. Los reportes de E1/E4 son históricos y no se reescriben.

## E6.2 — protección real de datos sensibles

**Verificado en API GitHub**: ruleset activo de rama principal **`main-production-integrity`**, ID **21661257**; tiene seis checks obligatorios (`Required merge gate`, `public-artifact-contract`, `reflow-sitewide`, `pa11y-baseline`, `lighthouse`, `Compare against committed baselines`) pero en el parámetro de revisión consta:

- `required_approving_review_count: 0`
- `require_code_owner_review: false`
- `dismiss_stale_reviews_on_push: false`
- `require_last_push_approval: false`
- Hay una entrada `bypass_actors` tipo `RepositoryRole` con `bypass_mode: always`; **no interpretar esto como ausencia de riesgos ni afirmar que todos los usuarios pueden saltarse reglas**, hay que comprobar su alcance con administración.

**Consecuencia:** la rama principal no impone revisión humana formal. El flujo actual de ingesta bibliográfica tiene CI real y puede fusionar su PR automática de libros; **no cambiar ese comportamiento desde #692**, ni abrir `data/editoriales.json` en su allowlist. Para integrar la actualización de manuscritos hacen falta **ambos** controles:
1. Un **contrato por campo, fail-closed**, que no permita atribuir `open/closed` a una declaración de grupo, a un correo general ni a una fuente caducada y que obligue a comparar la versión exacta del directorio.
2. **Un control de autorización GitHub externo a cualquier JSON escrito por el propio candidato**: revisión auténtica y preferiblemente protección por ruta `data/editoriales.json` (CODEOWNERS + reglas o ruleset con revisión específica si el plan/cuenta lo permite), controles de SHA y bloqueo de cambios sensibles por el bot. Requiere decisión del responsable del repositorio porque 1 aprobación global podría bloquear la automatización legítima de libros.

Documentación oficial: [branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [revisión específica por ficheros en rulesets (17/02/2026)](https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/). La disponibilidad exacta de reglas granulares de equipos depende del tipo de repositorio y cuenta, **no verificada para este usuario**. No se han cambiado reglas ni solicitado permisos administrativos.

### Cambios que requieren coherencia entre campos

El [builder público de editoriales en `main`](https://github.com/davidpd89/web-escritor/blob/main/scripts/build-editoriales.py) exige: `status` del catálogo `open/closed/indirect/award_only/unknown`, `verified_at` y `page_updated_at` con fechas válidas, `sources` con fuente primaria HTTPS y `history` completo. Para `closed` prohíbe `submission_email` público; no permite `submission_url` declarada como no disponible y `status=open`. Un parche sólo con `status` puede incumplir ese contrato o, peor, dejar datos engañosos.

**Campos de decisión definidos:**
- `status`: **implementado como revisión de intención NO autenticada**, sólo `open/closed` con prueba reciente, específica de la editorial, y coincidencia de valor previo; salida contiene lista de **campos acompañantes** que deben revisarse, pero no crea parche.
- `verified_at`, `page_updated_at`, `sources`, `history`, `direct_submission`, `submission_channel`, `submission_url`, `requirements`, `public_note`, `submission_email`: **revisión obligatoria en conjunto antes de un cambio público**, no soportados como escrituras automáticas por el prototipo; correos **nunca** proceden automáticamente de E4.
- `general_contact` y `press_contact`: registrados como objetivos distintos, **no existen como campos homogéneos en el esquema público actual**; requieren propuesta de esquema, licencia, procedencia y tratamiento de datos personales antes de publicar.
- `website_url` e identidad jurídica: deben verificarse fuera del estado de manuscritos y resolverse explícitamente si el sello es distinto de la empresa histórica (Bruguera).

**Código de investigación**: [`scripts/research/gpt_editoriales_approval_contract.py`](https://github.com/davidpd89/web-escritor/blob/research/gpt-editoriales-2026-10-22/scripts/research/gpt_editoriales_approval_contract.py). Lee `main` en JSON, salida de E4, tareas de E5 y manifiesto manual; comprueba SHA-256 de tres objetos, fecha, identidad, coincidencia exacta del valor anterior, tareas y pruebas E4, TTL y alcance individual. Resultado de solo lectura: `intents_for_external_review`, nunca `approved_patches`. Las palabras `decision: approve/reject` son **solicitud autoafirmada**, no una firma o revisión real de GitHub. `trusted_approval_verified=false`, `patch_generated=false`, `automated_merge_allowed=false`.

[`tests/test_gpt_editoriales_approval_contract.py`](https://github.com/davidpd89/web-escritor/blob/research/gpt-editoriales-2026-10-22/tests/test_gpt_editoriales_approval_contract.py): **20 casos sintéticos, escritos pero NO ejecutados**, sobre cambios de SHA/contenido, alcance grupo, fuentes antiguas, correo, identidad, rechazo, duplicados y tareas incompatibles.

## Integración futura: puerta de seguridad en tres etapas

```text
E3 (conciliar identidades) + E4 (evidencias verificadas)
     │              ├─ fuente/atribución/uso autorizado
     └──── E5 (proponer cola, sin publicación)
                     │
                E6 (intenciones SHA-256 y control campo a campo)
                     │
           revisión real por persona autorizada en GitHub
                     │
       PR de ingeniería/manuscritos separada, datos + HTML
       validaciones del builder, CI de commit actual, reglas sin bypass
                     │
                    merge manual
```

**Bloqueos antes de primera integración real:** revisar reglas de la rama principal, resolver si un responsable humano distinto puede aprobar la PR, fijar protección por ruta sin romper PRs de libros, ejecutar las **77 pruebas preparadas en los cinco módulos**, depurar contradicciones de esquemas e integrar con el constructor existente en otra PR no draft. `main` no se modifica desde esta investigación.

## Próximo «siguiente investigación de GPT» — E6.3

Preparar un **piloto de cinco candidatos, exclusivamente offline**, tomando identidad/E4/E5 coherentes con la instantánea actual de `main`, detectar errores reales de los scripts y contrastar la cola con revisión manual. El código está escrito pero **ningún test ni piloto se han ejecutado** por la política conservadora de esta investigación. Si se autoriza ejecutar pruebas sintéticas, hacerlas sin red y sin crear Actions, tras anotar el resultado; luego corregir defectos y evaluar ruta segura de integración.
