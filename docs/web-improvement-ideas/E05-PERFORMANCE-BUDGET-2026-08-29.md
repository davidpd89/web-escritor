# E.5 — Performance budget determinista por shell/familia

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`IMPLEMENT_AFTER_CURRENT_DEBT`**

## 1. Alcance

E.5 propuso incorporar un performance budget a CI para detectar crecimiento accidental de JS/CSS crítico. La investigación de #135 refinó la propuesta hasta convertirla en un contrato de **bytes y requests determinista del artifact**, complementario a Lighthouse y Core Web Vitals.

Esta PR recupera ese razonamiento completo. No crea aún el checker ni modifica CI.

## 2. Veredicto

**`IMPLEMENT_AFTER_CURRENT_DEBT`**.

El backlog neto sigue existiendo. En la revisión actual no se ha localizado una autoridad dedicada que modele budgets por shell/familia con baseline, umbral y margen deliberado.

El objetivo no es fallar builds por cualquier byte adicional. Es detectar regresiones materiales y exigir una decisión consciente cuando una familia supera el presupuesto acordado.

## 3. Hipótesis original

La idea inicial era sencilla:

> añadir un check que falle si JS/CSS crítico de una plantilla supera un umbral, complementando los tests de CLS.

La revisión detectó que un único límite global sería demasiado tosco y que thresholds de Lighthouse pueden ser ruidosos.

## 4. Evolución histórica

| Fase | Estado | Razón |
|---|---|---|
| Idea original | budget CI | Frenar crecimiento de JS/CSS crítico. |
| Revisión 108/108 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Budget determinista de bytes/request count + Lighthouse. |
| Matriz intermedia | `IMPLEMENTAR` | Baseline primero, umbrales con margen razonable. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Budget por shell/familia; no sustituye CWV. |
| Pasadas tardías | reforzada | R.57 Coverage: medir antes de dividir/eliminar CSS/JS. |
| Revalidación independiente | mantenida | No aparece duplicado que cierre la idea. |
| `main` actual | backlog neto | No se ha localizado checker/manifest de performance budget equivalente. |

## 5. Qué problema resuelve

El sitio puede degradarse sin que una PR rompa funcionalidad.

Ejemplos:

- añadir otra hoja global a todas las páginas;
- cargar una librería por un componente minoritario;
- duplicar una fuente;
- crecer `script.js` con código muerto;
- incorporar terceros o assets que se cargan en todas las rutas;
- aumentar imágenes críticas sin darse cuenta.

Un budget vuelve visible ese coste antes de mergear.

## 6. Por qué debe ser determinista

#135 diferenció dos familias de señal:

### Artifact budget

Mide cosas reproducibles a partir del build:

- bytes de CSS;
- bytes de JS;
- fonts;
- media crítica si se decide incluirla;
- número de requests declarados por shell/familia;
- peso total de determinados conjuntos.

### Runtime/performance lab

Lighthouse/Playwright/traces observan carga/render/interacción.

El primer grupo es mucho más estable como gate de PR. El segundo aporta contexto y experiencia, pero puede variar por entorno.

## 7. No usar un solo límite global

La arquitectura del sitio tiene familias con necesidades diferentes.

Una herramienta de análisis local puede necesitar más JS que una ficha editorial. Un artículo puede tener menos interacción pero más imágenes.

#135 propuso budgets por:

- shell común;
- familia de página;
- recurso relevante.

Ejemplo conceptual:

```json
{
  "shell": {
    "cssBytes": 180000,
    "jsBytes": 120000,
    "fontBytes": 250000
  },
  "families": {
    "article": { "extraJsBytes": 20000 },
    "tool": { "extraJsBytes": 180000 }
  }
}
```

Los números anteriores son ilustrativos; **no son thresholds aprobados**.

## 8. Baseline antes de umbral

Secuencia correcta:

1. medir artifact actual;
2. agrupar por shell/familia;
3. detectar outliers/deuda existente;
4. decidir qué estado se acepta como baseline;
5. añadir margen razonable;
6. documentar cómo se eleva un budget;
7. solo entonces hacerlo gate.

No elegir 100 KB porque una guía genérica diga que “100 KB es bueno”.

## 9. Qué contar

La futura implementación debe definir explícitamente si usa:

- bytes sin comprimir;
- gzip/brotli estimado;
- ambos;
- request count;
- recursos locales solamente;
- terceros por inventario separado.

Para CI determinista, los bytes en disco y conjuntos de archivos son una base sólida. La compresión live pertenece a E.7 y no debe mezclarse como dato supuesto.

## 10. Qué NO contar ciegamente

- assets versionados pero no consumidos;
- archivos de tests/docs;
- todas las imágenes del repo para cada ruta;
- pagefind completo como si cada navegación descargara todo;
- media que no participa en una familia concreta;
- terceros como bytes locales inexistentes.

El budget debe reflejar el artifact y rutas reales.

## 11. R.57 — Coverage como complemento

La décima pasada investigó Chrome DevTools Coverage.

Conclusión relevante:

> detectar bytes de CSS/JS no usados es fácil; decidir qué eliminar o dividir depende de arquitectura.

Por tanto, si E.5 detecta crecimiento alto:

1. no partir bundles automáticamente;
2. usar Coverage en rutas/journeys representativos;
3. abrir componentes dinámicos antes de declarar código “unused”;
4. revisar cache reuse entre páginas;
5. refactorizar solo con evidencia.

## 12. Relación con E.1

Si el budget detecta exceso de imágenes, E.1 puede reducir bytes mediante formatos/tamaños modernos. Pero E.5 no debe manipular automáticamente la escalera de imágenes.

## 13. Relación con E.2

Un budget de JS pequeño no garantiza buen INP. E.2 analiza coste de ejecución e interacción.

Por tanto:

```text
E.5 = cuánto enviamos
E.2 = qué ocurre cuando interactuamos
```

## 14. Relación con E.3/E.4

Preload/fetchpriority alteran prioridad y orden, no necesariamente peso total. E.5 puede registrar request count/bytes, pero el waterfall decide si el hint es correcto.

## 15. Relación con E.8

Terceros necesitan su propio inventario de dominio, loader, privacidad, CSP, owner y coste. E.5 puede reflejar una estimación en reporting, pero no debe duplicar `third-party-integrations` como autoridad.

## 16. Arquitectura de checker sugerida

Una implementación compatible con la filosofía del repo podría ser:

```text
data/performance-budgets.json
scripts/check-performance-budgets.py
reports/performance-budget.json
```

El nombre exacto debe adaptarse a la arquitectura vigente al implementar.

El checker debería:

1. cargar manifest de budgets;
2. resolver archivos reales del artifact;
3. calcular bytes determinísticamente;
4. comparar baseline/limit;
5. reportar top contributors;
6. fallar únicamente cuando se excede un contrato marcado como gate;
7. permitir `--report` sin mutar archivos.

## 17. Cómo elevar un budget

No editar el número silenciosamente para poner CI verde.

Una subida debe incluir:

- contributor que creció;
- bytes before/after;
- motivo producto/técnico;
- alternativas evaluadas;
- impacto runtime si procede;
- decisión explícita de aceptar el nuevo coste.

Esto convierte el budget en una herramienta de gobernanza, no una cifra ornamental.

## 18. Margen razonable

Un threshold exactamente igual al baseline hace que pequeñas diferencias legítimas generen ruido.

La política debería admitir:

- margen porcentual o absoluto pequeño;
- budget diferenciado para nuevas familias;
- excepción temporal con owner/fecha si hay deuda real;
- nunca un “+50% para que deje de fallar” sin rationale.

## 19. Reporting útil

Salida esperable:

```text
family: article
status: PASS
css: 143.2 KB / 160 KB
js: 96.5 KB / 110 KB
fonts: 182 KB / 200 KB
requests: 14 / 16
largest contributors:
  v1-...css
  script.js
  yellowtail....woff2
```

Si falla, el artifact debe seguir disponible para diagnosticar.

## 20. CI

Integrar en el Required merge gate solo cuando:

- baseline sea estable;
- checker tenga tests;
- rutas/conjuntos estén bien definidos;
- el gate no dependa de red externa;
- exista procedimiento documentado de actualización.

Antes puede ejecutarse como report-only para recoger baseline.

## 21. No hacer

- budgets universales copiados de otro proyecto;
- threshold Lighthouse temporal como único gate;
- medir solo tamaño minificado de un bundle ignorando fonts/CSS;
- sumar todo `/assets/` como si se descargara por página;
- fallar por 1 byte sin margen;
- elevar límite automáticamente;
- minificar/refactorizar a ciegas para “ganar CI”;
- eliminar accesibilidad/contenido para bajar peso;
- confundir compresión live con bytes en repo.

## 22. Estado actual de `main`

El repositorio tiene:

- Lighthouse CI;
- múltiples QA de browser;
- checkers de assets/imagen;
- contratos de artifact público.

Pero en la inspección actual no se ha localizado una autoridad dedicada equivalente a un **budget determinista por shell/familia**.

Por ello E.5 no pasa a `ALREADY_COVERED`.

## 23. DoD futuro

- baseline documentado;
- manifest de budgets versionado;
- checker determinista;
- tests unitarios/fixtures;
- report de contributors;
- familias justificadas;
- margen deliberado;
- procedimiento de elevar budget;
- modo report-only inicial;
- gate solo tras estabilización;
- Lighthouse/CWV siguen siendo capas complementarias.

## 24. Pasadas tardías

R.57 (Chrome DevTools Coverage) es el añadido posterior más relevante. No cambia el estado: mejora el procedimiento de diagnóstico cuando un budget señala CSS/JS excesivo.

La revalidación independiente mantiene E.5.

## 25. Estado de verdad

- `DOCUMENTED`: sí.
- `IMPLEMENTED_IN_PR`: no.
- `MERGED_MAIN`: no.
- checker dedicado en `main`: no localizado.
- `CONFIGURED_LIVE`: no aplica.
- `VERIFIED_E2E`: no.

## 26. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-DECIMA-PASADA-NATIVA-GRATUITA-2026-08-28.md` (R.57).

Fuente primaria destacada:

- web.dev — Performance budgets 101.

## 27. Conclusión

E.5 conserva **`IMPLEMENT_AFTER_CURRENT_DEBT`**. El repositorio tiene muchas capas de QA de rendimiento, pero #135 identificó un hueco distinto: controlar de forma determinista cuánto artifact se envía por shell/familia y hacer explícitas las decisiones cuando ese coste crece. El budget debe nacer de un baseline real y complementar —no sustituir— Lighthouse, CWV, Coverage e INP.