# 03 — Deploy, verificación de producción, rollback y operación

## 1. Contrato de release

Un release no termina cuando `actions/deploy-pages` devuelve success.

Termina cuando:

1. el artifact permitido se construye;
2. el artifact pasa su contrato;
3. GitHub Pages acepta el deployment;
4. el dominio público sirve rutas críticas;
5. las clases internas siguen sin ser accesibles;
6. las superficies machine-readable mínimas responden;
7. canonical/JSON-LD de las rutas principales siguen coherentes.

Esta PR convierte esos pasos en:

```text
BUILD -> DEPLOY -> VERIFY PRODUCTION
```

## 2. Build

Autoridad:

`scripts/build-public-dist.py`

El workflow conserva:

```bash
python scripts/build-public-dist.py --out .preview-dist
python scripts/build-public-dist.py --check-contents --out .preview-dist
```

No publicar el root completo del repo.

No sustituir el allowlist-first por una denylist creciente.

No añadir ficheros técnicos al artifact para facilitar debugging.

## 3. Deploy

Autoridad:

`.github/workflows/deploy-pages.yml`

El job `deploy` usa:

`actions/deploy-pages@v4`

con environment `github-pages`.

El deploy depende de `build`, por lo que no debe ejecutarse si el artifact no se construye o no pasa el contrato.

## 4. Verify production

Nuevo job:

`Verify production after deploy`

Depende de `deploy`.

### Target

```text
https://davidportodiaz.com
```

No usar la URL de staging como sustituto de la comprobación final.

### TLS

Estricto.

No usar:

```text
SMOKE_INSECURE_TLS=1
STAGING_SMOKE_INSECURE_TLS=1
NODE_TLS_REJECT_UNAUTHORIZED=0
```

en producción.

Un certificado inválido es un incidente de producción, no una molestia del test.

## 5. Reintentos

El workflow permite hasta 3 ejecuciones completas del smoke con 15 segundos entre ellas.

Motivo: tolerar un retraso corto entre la finalización de la acción de Pages y la disponibilidad consistente del custom domain/CDN.

No se hacen:

- reintentos infinitos;
- sleeps de varios minutos que oculten un release roto;
- `continue-on-error`;
- conversión del fallo en warning.

Después del tercer fallo, el deployment workflow queda rojo.

## 6. Qué verifica el smoke

El fichero mantiene su nombre histórico:

`tests/test-staging-smoke.mjs`

pero su contrato es genérico.

### 6.1 Rutas públicas críticas

Actualmente:

- `/`;
- `/las-manecillas-del-recuerdo/`;
- `/libros/samuel-entre-mundos/`;
- `/cuaderno/`;
- `/herramientas/`.

Contrato:

- HTTP 200;
- `<title>` no vacío.

No pretende visitar las 50+ URLs públicas: es una sonda de release de señal alta y tiempo corto.

El crawl exhaustivo pertenece a otras suites.

### 6.2 Machine-readable mínimo

- `/robots.txt`;
- `/sitemap.xml`;
- `/llms.txt`.

Cada uno debe responder 200 y contener un marcador básico que reduzca falsos 200 de una página de error.

### 6.3 JSON-LD

Home y Manecillas deben contener al menos un bloque JSON-LD parseable.

Esto no sustituye los contratos machine-authority del repo. Detecta corrupción de HTML/output servido.

### 6.4 Canonical

Home:

```text
https://davidportodiaz.com/
```

Manecillas:

```text
https://davidportodiaz.com/las-manecillas-del-recuerdo/
```

El staging también puede ejecutar este check porque el canonical correcto de un preview debe seguir apuntando a producción, no a la URL del preview.

### 6.5 Frontera negativa HTTP

Deben ser 404:

```text
/scripts/
/tests/
/data/
/docs/
/qa/
/lab/
/migrations/
/.env.example
/lecturas/
/publicar-web/
/editorial-facts.json
/cloudflare-worker-subscribe.js
/cloudflare-worker-assistant.js
/wrangler.assistant.jsonc
/package.json
/package-lock.json
/lighthouserc.json
/press-kit/package-manifest.json
/donde-empieza-la-jaula/
```

Esta lista no es la autoridad primaria de publicación. La autoridad sigue siendo el builder allowlist-first.

El smoke es una defensa externa independiente: confirma que la capa realmente servida no expone ejemplos representativos de clases prohibidas.

## 7. Qué NO verifica el smoke

No concluir a partir de `PRODUCTION SMOKE PASS` que:

- todas las páginas son visualmente correctas;
- no existen errores de accesibilidad;
- todos los enlaces externos funcionan;
- todos los formularios completan su backend;
- Core Web Vitals de campo son buenos;
- todos los assets del service worker están frescos;
- Cloudflare/Brevo/Workers están configurados correctamente;
- Search Console ha rastreado el release;
- los crawlers de IA ya han actualizado caché;
- la compra de Manecillas existe.

El smoke valida salud mínima del release servido.

## 8. Incidente: production smoke rojo después de deploy

### Paso 1 — congelar

No mergear otro cambio encima «para ver si se arregla».

Identificar:

- SHA desplegado;
- run de Deploy Pages;
- qué assertion falla;
- si falló 1, 2 o los 3 intentos.

### Paso 2 — clasificar

#### A. Ruta pública 404/5xx

Revisar:

- artifact manifest/build;
- Pages deployment;
- custom domain;
- DNS/CDN;
- CNAME;
- rutas/case sensitivity.

#### B. Ruta interna devuelve 200

**Severidad alta.**

Congelar releases.

Determinar si:

- el artifact contiene el fichero;
- Pages está sirviendo un artifact anterior/distinto;
- otro origen/CDN está respondiendo;
- una regla de routing expone el árbol bruto.

No «arreglar» el smoke para aceptar 200.

#### C. Canonical incorrecto

Revisar la fuente HTML/build. No tolerar canonical de staging o dominio alternativo en producción sin decisión explícita.

#### D. JSON-LD roto

Comparar el HTML fuente del SHA con la respuesta pública. Si fuente está bien y producción no, investigar release/cache.

#### E. TLS / DNS / timeout

No desactivar TLS.

Comprobar dominio, DNS, Pages/Cloudflare y estado de certificado.

## 9. Rollback manual V1

No hay auto-rollback en esta iniciativa.

### 9.1 Elegir target

Preferencia:

- último SHA de `main` demostrado sano;
- idealmente un release tag futuro;
- no elegir «HEAD~1» automáticamente si hubo varios cambios o el problema es externo.

### 9.2 Estrategia Git recomendada

Para `main` protegido, preferir **revert mediante PR** de los commits causantes.

Ventajas:

- conserva historial;
- pasa required gates;
- deja causa visible;
- no fuerza refs.

### 9.3 Emergencia

Si producción está gravemente rota y el flujo normal es materialmente demasiado lento, usar el mecanismo de bypass documentado solo con intervención consciente del propietario.

Después:

- registrar motivo;
- ejecutar QA del hotfix;
- verificar producción;
- restaurar el flujo PR normal inmediatamente.

### 9.4 Verificación post-rollback

El rollback no está cerrado hasta:

```text
Deploy Pages -> success
Verify production after deploy -> success
```

## 10. Artifact identity — mejora P1 futura

El smoke actual puede verificar contrato, pero no demuestra criptográficamente que la respuesta HTTP sea exactamente el SHA recién desplegado.

Mejora recomendada futura:

### Opción preferida

Generar dentro del artifact un fichero público mínimo, por ejemplo:

```text
/release.json
```

con:

```json
{
  "commit": "<GITHUB_SHA>",
  "builtAt": "<release build timestamp or deterministic release id>"
}
```

**Solo** si se decide que exponer el SHA es aceptable y no crea otro contrato mutable innecesario.

El post-deploy smoke podría exigir que `commit == GITHUB_SHA`.

### Alternativa

Usar una huella de artifact/manifest fuera de la superficie pública y consultar API de deployment si ofrece una correlación suficiente.

No implementar en esta PR sin estudiar implicaciones de cache/privacidad/valor.

## 11. Forms canary — P1 futura

Un release puede tener HTML sano y un formulario roto.

Pero el canary no debe crear contactos reales en Brevo en cada deploy.

Diseño recomendado:

- staging/mock contract para payloads y errores — ya cubierto en gran parte;
- endpoint/flag de canary solo si puede comprobar infraestructura sin crear PII/contacto;
- producción live end-to-end manual en momentos de release importantes, usando una cuenta/control explícito y limpiable;
- nunca enviar emails ficticios aleatorios a Brevo.

## 12. Hydrated DOM crawl — P1 futura

Los checkers estáticos no ven todos los enlaces/estados creados por JS.

Añadir una pasada Playwright post-build o pre-merge que:

1. cargue las rutas públicas principales;
2. espere hidratación estable;
3. recoja `a[href]` finales;
4. detecte rutas internas imposibles y anchors vacíos;
5. no haga HEAD/GET masivos a terceros en el mismo gate;
6. separe enlace DOM inválido de disponibilidad de tercero.

No duplicar Lychee.

## 13. Production headers — P1 futura

Añadir una sonda específica para:

- HTTPS;
- redirect HTTP→HTTPS;
- CSP/headers que realmente entregue la capa pública;
- cache headers en HTML/assets;
- content-type correcto de HTML/JSON/XML/JS/CSS;
- service worker content-type/scope.

Debe verificar la red real, no inferirla desde HTML fuente.

## 14. Releases/tags — P1 futura

Para simplificar rollback:

- crear tag/release para hitos importantes;
- asociar SHA, fecha y evidencia;
- no taggear cada commit trivial;
- como mínimo: prelaunch estable, launch 03/09, postlaunch estable.

## 15. GitHub Pages environment

El job actual usa environment `github-pages`.

Después de estabilizar el flujo se puede evaluar:

- restricciones de branches que pueden desplegar;
- protección del environment;
- approvals solo si aportan valor real.

No añadir aprobación manual a cada deploy por reflejo: con PR protegida + required gates puede crear fricción sin señal adicional para un único mantenedor.

## 16. Definition of Done operacional

- [ ] build usa artifact allowlist-first;
- [ ] deploy depende de build;
- [ ] verify-production depende de deploy;
- [ ] producción se comprueba con TLS estricto;
- [ ] rutas públicas críticas 200;
- [ ] machine routes 200;
- [ ] canonical crítico correcto;
- [ ] JSON-LD crítico parseable;
- [ ] clases internas representativas 404;
- [ ] fallo persistente de smoke deja workflow rojo;
- [ ] no existe `continue-on-error` en production verify;
- [ ] rollback manual documentado;
- [ ] no existe auto-rollback opaco;
- [ ] el equipo/propietario sabe distinguir deploy success de production success.

## 17. Fuente oficial GitHub Pages / environments

- `https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages`
- `https://docs.github.com/en/actions/deployment/targeting-different-environments/managing-environments-for-deployment`

Volver a comprobar estas fuentes si se modifica la arquitectura de Pages o el plan de GitHub.
