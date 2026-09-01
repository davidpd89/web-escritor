# M.3 · Revalidación de producción · cabeceras obsoletas

Fecha: 2026-08-30  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Evidencia live upstream: PR #244 / M.1, run `33325462091`

## Veredicto

`SATISFIED_BY_M1_DRAFT · LIVE_BASELINE_CLEAN · NO_DUPLICATE_AUDITOR · NO_CODE_IN_M3`

La condición que mantenía M.3 pendiente ya se ha observado en la PR #244: el auditor live de M.1 inspecciona también las cabeceras legacy que M.3 quería inventariar.

## Evidencia live

En la entrada HTTP y las siete familias HTTPS muestreadas por M.1 no se observaron:

```text
X-XSS-Protection
Expect-CT
Public-Key-Pins
```

El patrón fue uniforme y `server: GitHub.com` confirmó además la capa que entrega las respuestas.

Por tanto no existe hoy una cabecera legacy de esas tres familias que retirar en la muestra de producción.

## Revalidación oficial

La documentación MDN actual confirma que:

- `X-XSS-Protection` está deprecado/no estandarizado y no debe reintroducirse como sustituto de CSP;
- `Expect-CT` está deprecado y Chromium dejó de necesitarlo porque Certificate Transparency se aplica por defecto;
- HPKP / `Public-Key-Pins` es una característica de seguridad obsoleta.

M.3 debe conservar estos nombres como detecciones negativas de regresión, no como recomendaciones de configuración.

## Relación con PR #244

La PR #244 añade `qa/live-security-headers.mjs`, que ya registra:

- `x-xss-protection`;
- `expect-ct`;
- `public-key-pins`;
- contradicciones potenciales entre CSP meta y CSP HTTP mediante la observación de la cabecera live;
- redirects y variaciones por familia de rutas.

Crear otro `check-obsolete-headers.*` en M.3 duplicaría owner y violaría el contrato de #135.

Mientras #244 siga DRAFT/no mergeada, M.3 debe declarar explícitamente esta dependencia: el trabajo queda satisfecho **por la implementación upstream propuesta**, no por `main` todavía.

## Qué queda por vigilar

Si en futuros runs aparece cualquiera de las cabeceras legacy:

1. identificar la capa que la introdujo;
2. confirmar que no es una lectura falsa/intermedia de redirect;
3. retirarla en su owner real;
4. repetir el auditor live;
5. no sustituirla por otra cabecera solo por checklist.

## Qué NO hacer

- crear un segundo auditor HTTP;
- añadir `X-XSS-Protection` para navegadores modernos;
- reintroducir `Expect-CT`;
- recuperar HPKP;
- considerar ausencia en repo como prueba si el auditor live desaparece;
- hacer hard fail del merge por una lista heredada sin baseline/ownership.

## Estado final

No hay código propio que implementar en M.3. La acción correcta es **reutilizar y conservar el auditor de M.1** y tratar una aparición futura de estas cabeceras como regresión/operación de hosting.
