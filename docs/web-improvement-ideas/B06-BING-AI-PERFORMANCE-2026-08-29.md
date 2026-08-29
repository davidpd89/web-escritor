# B.6 · Bing Webmaster Tools + AI Performance

Fecha de reconstrucción: 2026-08-29

Idea original: tratar Bing Webmaster Tools como una fuente propia de datos, separada de Google Search Console, especialmente por la nueva superficie AI Performance.

Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.

Estado final: `EXTERNAL_OPERATION`.

## Veredicto reconciliado

**EXTERNAL_OPERATION. BING AI PERFORMANCE MERECE USARSE, PERO CONFIGURAR/VERIFICAR LA PROPIEDAD ES UNA OPERACIÓN DE CUENTA, NO CÓDIGO DEL REPO.**

B.6 es un buen ejemplo de por qué conservar la historia de #135 importa. La primera revisión la clasificó `IMPLEMENT_NOW`; una pasada posterior corrigió la naturaleza de la tarea: no había que fabricar código para “implementar Bing”, sino verificar/configurar la propiedad real y capturar un baseline en Bing Webmaster Tools. La autoridad final conserva esa corrección.

## 1. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` propuso separar activamente Search Console y Bing Webmaster Tools porque Bing incorporó en 2026 un reporte específico de citaciones de IA.

La hipótesis original también recogía afirmaciones de fuentes secundarias sobre la relación entre índices/proveedores. La decisión final **no depende de esas afirmaciones secundarias**: se sostiene por una capacidad oficial de Bing verificable directamente.

## 2. Evolución cronológica en #135

### 2.1 · Revisión exhaustiva → `IMPLEMENT_NOW`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` consideró B.6 de alto valor y bajo coste porque Bing AI Performance aporta señales de visibilidad generativa que Search Console no sustituye.

### 2.2 · Override de decisión → `EXTERNAL_OPERATION`

`docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` hizo la corrección material:

> Bing AI Performance es útil, pero se configura/consulta en la cuenta Bing; no es código del repo.

Instrucción de #135:

- verificar/activar la propiedad cuando haya acceso;
- registrar evidencia y baseline;
- no abrir código ficticio para “implementar Bing”.

### 2.3 · Matriz final → `IMPLEMENTAR` como operación

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` mantuvo el valor práctico:

- Bing Webmaster Tools + AI Performance;
- importar/verificar propiedad si aún no existe;
- panel gratuito primero;
- API solo si más adelante existe una necesidad que el panel/export no resuelva.

### 2.4 · Autoridad final → `EXTERNAL_OPERATION`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó definitivamente:

> Bing Webmaster Tools + AI Performance es útil y gratuito. Configurar/verificar externamente si aún no existe; API solo si el panel/export deja de bastar.

### 2.5 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` mantuvo B.6 y volvió a citar documentación oficial de Bing/Clarity. No convirtió configuración externa en estado de repo.

Secuencia:

```text
hipótesis: activar Bing por separado
→ revisión: IMPLEMENT_NOW
→ override: la tarea real vive en cuenta/panel = EXTERNAL_OPERATION
→ matriz: usar panel/importación antes que API
→ autoridad final: EXTERNAL_OPERATION
→ revalidación: mantiene
```

## 3. Fuente primaria actual

Microsoft Bing Webmaster Blog, febrero de 2026:

https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview

La superficie AI Performance permite analizar, según Microsoft:

- **Total Citations**: veces que contenido del sitio fue citado en respuestas de IA cubiertas por el reporte;
- **Average Cited Pages**: promedio de páginas del sitio citadas por respuesta/resultado bajo la metodología del producto;
- **grounding queries** de ejemplo;
- actividad/tendencia de citas;
- páginas/URLs citadas.

La documentación oficial del producto debe prevalecer sobre interpretaciones de blogs GEO/SEO.

## 4. Lo que esas métricas NO significan

No presentar AI Performance como:

- posición de ranking;
- “autoridad IA” universal;
- cuota de todas las respuestas generativas de internet;
- prueba de causalidad entre un cambio SEO y una cita;
- garantía de tráfico;
- garantía de que una página es la fuente principal de una respuesta.

Son métricas de la cobertura/metodología de Bing Webmaster Tools.

## 5. Estado que debe registrarse

La taxonomía del proyecto importa:

```text
DOCUMENTED
≠ CONFIGURED_LIVE
≠ VERIFIED_E2E
```

Esta PR solo conserva la investigación. No puede afirmar que Bing Webmaster Tools está configurado en la cuenta por el hecho de existir documentación Git.

Estados operativos posibles:

- `NOT_CHECKED`;
- `PROPERTY_EXISTS`;
- `VERIFIED`;
- `AI_PERFORMANCE_AVAILABLE`;
- `BASELINE_CAPTURED`;
- `NOT_AVAILABLE_YET`.

Guardar fecha y evidencia factual, no credenciales.

## 6. Operación recomendada cuando se ejecute

1. entrar en Bing Webmaster Tools con la cuenta autorizada;
2. comprobar si `davidportodiaz.com` ya existe;
3. si no existe, usar un método oficial de alta/verificación, incluida importación desde Search Console cuando esté disponible y sea apropiada;
4. comprobar sitemap/indexación básica;
5. abrir AI Performance si la propiedad tiene acceso al reporte;
6. registrar baseline con ventana y fecha:
   - citas totales;
   - URLs citadas;
   - grounding queries visibles;
   - tendencia;
7. guardar solo datos necesarios y sin tokens/credenciales;
8. repetir con cadencia razonable dentro del benchmark B.5.

## 7. API: no ahora por defecto

No crear una integración API solo porque exista una cuenta.

Primero responder:

- ¿qué pregunta repetida no resuelve la UI/export?
- ¿qué frecuencia necesita automatización?
- ¿qué datos aporta la API realmente?
- ¿qué credencial/permiso requiere?
- ¿qué retención y mantenimiento introduce?

Si no hay una necesidad concreta, la interfaz de Bing es suficiente.

## 8. Relación con B.5 y Clarity

### B.5

AI Performance es una de las fuentes proveedor-específicas que alimentan el benchmark de citaciones. No sustituye ChatGPT/Gemini/Claude/Perplexity ni el corpus controlado.

### Clarity AI Citations

La pasada R.82 de #135 observó que Clarity AI Visibility puede verificar dominio mediante GSC o Bing Webmaster Tools sin necesidad de instalar tracking solo para citaciones.

Fuente:

https://learn.microsoft.com/en-us/clarity/ai-visibility/ai-citations

Eso aumenta el valor operativo de tener BWT correctamente verificado, pero no obliga a instalar Clarity ni su MCP.

## 9. Qué NO hacer

- crear scripts vacíos para simular implementación;
- versionar credenciales de Bing;
- afirmar `CONFIGURED_LIVE` sin observar la cuenta;
- inventar un baseline;
- mezclar citas con ranking orgánico;
- usar un “AI authority score” derivado arbitrariamente;
- asumir que una grounding query representa todo el prompt del usuario;
- automatizar la API antes de necesitarla;
- depender de la afirmación histórica de fuentes secundarias sobre qué índice usa cada producto para justificar B.6.

## 10. Evidencia mínima para cerrar la operación externa

Cuando se ejecute de verdad:

- propiedad exacta `davidportodiaz.com` visible;
- estado de verificación;
- fecha;
- AI Performance disponible/no disponible;
- primera ventana de datos o `NO_DATA` explícito;
- sitemap/diagnóstico relevante si aparece;
- sin exponer cuenta, tokens ni PII.

## 11. Definition of Done

### Reconstrucción

- [x] hipótesis original preservada;
- [x] `IMPLEMENT_NOW` inicial preservado;
- [x] override `EXTERNAL_OPERATION` preservado;
- [x] matriz “panel primero/API después” preservada;
- [x] autoridad final preservada;
- [x] revalidación independiente preservada;
- [x] Bing AI Performance oficial revalidado.

### Operación futura

- [ ] propiedad comprobada/verificada;
- [ ] disponibilidad AI Performance comprobada;
- [ ] baseline guardado o `NO_DATA`;
- [ ] integración con B.5;
- [ ] API solo si existe necesidad posterior.

## 12. Trazabilidad #135

Aportan contenido específico:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/ai-discoverability/08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md`.

Las restantes pasadas/fuentes fueron revisadas y no cambian el estado final.

## 13. Recomendación

**MERGE como reconstrucción completa + `EXTERNAL_OPERATION`.** Después, ejecutar la comprobación real de cuenta cuando haya acceso; no confundir este documento con configuración live.