# npm supply-chain baseline · 27/08/2026

**Estado:** baseline de continuidad creado a partir de la auditoría realizada durante PR #127 y de la revalidación posterior.  
**No es una certificación de seguridad.** Su función es evitar que las conclusiones queden solo en el cuerpo de una PR y se pierdan cuando cambie el árbol.

## 1. Qué se observó

La instalación auditada reportó:

```text
13 vulnerabilities
2 low
1 moderate
10 high
```

La investigación de #127 concluyó que las advisories observadas estaban en dependencias transitivas de las herramientas de CI/dev `@lhci/cli` y `pa11y-ci`, no en el artefacto HTML/CSS/JS publicado.

Familias de paquetes mencionadas durante esa investigación:

- `extract-zip`;
- `tmp`;
- `uuid`;
- `inquirer` / `external-editor`;
- `puppeteer` / `puppeteer-core` / `@puppeteer/browsers`;
- `lighthouse`.

Los dos paquetes directos señalados por esa ruta estaban ya en las versiones usadas por el repo:

- `@lhci/cli@0.15.1`;
- `pa11y-ci@4.1.1`.

La conclusión operativa registrada fue: no existía en ese corte un `npm audit fix` seguro que eliminase el conjunto sin forzar cambios/downgrades inadecuados, y `npm audit fix --force` no debía ejecutarse a ciegas.

## 2. Qué NO está suficientemente preservado todavía

El resumen anterior no basta para cerrar supply-chain de forma durable. Falta incorporar aquí (o en un JSON hermano machine-readable) el resultado advisory-by-advisory de la sesión original.

Para cada advisory real, registrar:

| Campo | Obligatorio |
|---|---|
| advisory/GHSA/CVE o identificador que devuelva npm | sí |
| paquete afectado | sí |
| rango afectado | sí |
| versión instalada | sí |
| dependencia directa/transitiva | sí |
| path(s) que la introducen | sí |
| producción/browser vs CI/dev-only | sí |
| función vulnerable | sí |
| reachability en cómo este repo usa la dependencia | sí, con explicación |
| versión corregida disponible | sí |
| upgrade mínimo viable | sí |
| riesgo/breaking change | sí |
| decisión | `upgrade`, `accept-temporarily`, `remove`, `monitor` |
| owner | sí |
| `reviewBy` | sí |
| fuente primaria | advisory/vendor/release exacta |

Hasta que esas filas estén presentes, la frase correcta es:

> «La auditoría de #127 encontró que el contador procede de tooling CI/dev y no identificó una ruta explotable en el uso observado; falta conservar el detalle advisory-by-advisory en una autoridad versionada.»

No decir simplemente «las 13 vulnerabilidades no importan».

## 3. Regla de reachability

La clasificación debe responder a **cómo se ejecuta el código vulnerable**, no solo a `devDependency=true`.

Ejemplos de razonamiento válido:

```text
paquete vulnerable
→ lo introduce @lhci/cli
→ solo se instala/ejecuta en runner de CI
→ la función afectada aparece en X camino
→ nuestro invocation path no llama X porque ...
→ riesgo residual ...
```

Razonamiento insuficiente:

```text
es devDependency → seguro
```

Un compromiso de supply chain, postinstall o input hostil en CI puede seguir siendo material aunque nada llegue al navegador.

## 4. Política de actualización

1. `npm audit fix --force` está prohibido como respuesta automática a un contador.
2. Si aparece una versión segura compatible de un paquete directo, abrir PR pequeña de upgrade + CI.
3. Si el advisory cambia de severidad/alcance o se vuelve reachable en nuestro uso, reabrir inmediatamente la decisión.
4. Si el árbol deja de necesitar una dependencia vulnerable, preferir eliminación a mantener aceptación perpetua.
5. Toda aceptación temporal debe tener `reviewBy`; no crear excepciones sin caducidad.

## 5. Check recomendado

No crear un workflow que falle eternamente porque el baseline conocido contiene 13 entradas ya evaluadas.

El check útil debe detectar:

- advisory nueva;
- advisory conocida que cambia de severidad/rango;
- cambio del dependency path;
- nueva versión corregida disponible;
- desaparición de una advisory conocida;
- expiración de `reviewBy`.

Puede mantenerse un JSON machine-readable, por ejemplo:

```text
data/supply-chain-npm-baseline.json
```

El Markdown explica decisiones; el JSON permite diff/CI.

## 6. DoD de este frente

- [ ] pegar/normalizar las 13 advisories reales con IDs y paths exactos del audit original o repetir `npm audit --json` en el HEAD actual;
- [ ] contrastar cada advisory con fuente primaria vigente;
- [ ] registrar reachability y decisión individual;
- [ ] añadir owner + reviewBy;
- [ ] añadir baseline machine-readable si aporta señal;
- [ ] añadir CI que detecte cambios sobre el baseline, no que silencie ni fuerce fixes;
- [ ] actualizar #120 para enlazar esta autoridad en vez de repetir una conclusión resumida;
- [ ] no exponer tokens, rutas privadas ni datos de runner innecesarios.
