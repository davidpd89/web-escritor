# Protección anti-scraping del correo público — 2026-09-08

Owner: PR `feat/email-antispam-protection-2026-09-08`  
Estado: **PARTIAL_IMPLEMENTATION · RUNTIME_AND_AUDITOR_READY · MARKUP_MIGRATION_PENDING**

## Objetivo

Reducir el harvesting automático del correo público de David Porto Díaz sin esconderlo a personas reales ni romper prensa, librerías, lectores, teclado, lector de pantalla o el caso sin JavaScript.

La protección debe ser deliberadamente ligera y usable: **no CAPTCHA para ver un email, no Turnstile, no login, no cookies, no tracking y no servicio externo**.

Esta capa no pretende hacer que el correo sea secreto. Una persona, un bot con navegador que interactúe con la página o cualquier tercero que ya conozca la dirección puede seguir utilizándola. El objetivo realista es eliminar el camino de coste cero que hoy permite cosecharla leyendo HTML estático.

## Hallazgo actual

El sitio ya intenta proteger el email, pero la técnica actual es insuficiente.

### Footer global

`scripts/build-site-shell.py` define el correo en texto plano como `AUTHOR_EMAIL` y `obfuscated_mailto()` lo serializa con referencias numéricas HTML (`&#100;&#97;...`).

El resultado no contiene `@` ni `mailto:` en texto literal, pero un parser HTML estándar decodifica esas entidades automáticamente. Para un scraper moderno equivale prácticamente a publicar la dirección.

Además, el footer generado se replica en las páginas V1, por lo que la exposición no está confinada a una sola URL.

### Prensa

`prensa.html` contiene varios `mailto:` codificados también con entidades numéricas, entre ellos:

- CTA de cabecera «Contactar para prensa»;
- solicitud de portada de `Samuel entre mundos`, donde además se muestra visualmente la dirección;
- «Solicitar entrevista»;
- «Escribir a prensa» para presentaciones/firmas;
- «Solicitar ejemplar» para reseñas;
- cualquier otra CTA mailto que aparezca al hacer el scan final.

Por tanto, cambiar solo el footer no serviría.

## Contrato nuevo

### 1. El HTML público NO contiene la dirección

El HTML desplegado no debe contener:

- la dirección en texto plano;
- `mailto:<dirección>`;
- la dirección codificada con entidades HTML;
- el `mailto:` codificado con entidades HTML;
- la dirección en atributos `data-*`, JSON-LD o metadata.

El correo tampoco es necesario en `Person.email` de Schema.org para que la entidad de autor funcione, así que no debe añadirse al JSON-LD como atajo.

### 2. El usuario conserva acceso directo

Las superficies de contacto usan un enlace real de fallback, por ejemplo:

```html
<a
  class="footer-email"
  href="/prensa.html#contacto"
  data-email-reveal
  data-email-label-after="Abrir correo"
>Mostrar correo</a>
```

Sin JS, el enlace funciona y lleva a la sección de contacto.

Con JS, `assets/email-reveal.js` intercepta la activación, construye localmente la dirección, sustituye el trigger por un `<a href="mailto:...">` real, muestra la dirección o etiqueta indicada y mueve el foco al enlace revelado.

Esto mantiene:

- ratón;
- teclado;
- foco visible;
- screen reader;
- funcionamiento no-JS razonable;
- cero red/telemetría;
- CSP `script-src 'self'` compatible.

### 3. Las CTAs de prensa conservan asunto

Ejemplo:

```html
<a
  class="primary-action"
  href="#contacto"
  data-email-reveal
  data-email-subject="Entrevista — David Porto Díaz"
  data-email-label-after="Abrir correo para entrevista"
>Solicitar entrevista</a>
```

El runtime genera el `mailto:` con `URLSearchParams`; no concatenar asuntos manualmente en HTML.

Asuntos que deben preservarse respecto a las CTAs actuales:

- `Prensa — David Porto Díaz`;
- `Portada Samuel entre mundos`;
- `Entrevista — David Porto Díaz`;
- `Presentación o firma — David Porto Díaz`;
- `Solicitud de ejemplar de reseña`.

Si el scan descubre más CTAs, conservar su intención mediante `data-email-subject` sin publicar el destino.

## Implementación ya incluida en esta PR

### `assets/email-reveal.js`

- no contiene la dirección en texto plano;
- la construye desde códigos de caracteres;
- solo actúa sobre `[data-email-reveal]`;
- no hace `fetch` ni peticiones externas;
- revela tras interacción humana;
- crea `mailto:` con subject/body opcionales;
- mantiene clase/id del trigger;
- mueve el foco al enlace real;
- puede anunciar el resultado mediante un status existente (`data-email-status`).

La representación por character codes es **ofuscación**, no secreto. El valor es que el email desaparece del HTML estático y de los scrapers que no recorren/ejecutan la aplicación.

### `scripts/audit-public-email-exposure.py`

Audita artefactos públicos y detecta tanto:

- plaintext;
- como la ofuscación antigua por entidades HTML, usando `html.unescape()`.

Modo inicial:

```bash
python scripts/audit-public-email-exposure.py
```

Modo gate tras la migración:

```bash
python scripts/audit-public-email-exposure.py --strict
```

El modo `--strict` debe quedar en CI una vez que el resultado sea 0.

### `tests/test-email-protection.py`

Protege el auditor frente a:

- correo literal;
- mailto literal;
- entidades numéricas HTML;
- trigger interactivo seguro;
- exclusión de documentación de la superficie pública.

## Migración pendiente — hunks pequeños para Claude

No reemplazar enteros `scripts/build-site-shell.py`, `prensa.html` ni JS globales. Aplicar hunks mínimos desde `main` actualizado.

### A. `scripts/build-site-shell.py`

1. Eliminar:

```python
AUTHOR_EMAIL = "..."
```

y `obfuscated_mailto()`.

2. Añadir un helper sin dirección, por ejemplo:

```python
def email_reveal_link(label: str = "Mostrar correo", *, css_class: str = "footer-email", subject: str | None = None) -> str:
    attrs = [
        f'class="{css_class}"',
        'href="/prensa.html#contacto"',
        'data-email-reveal',
    ]
    if subject:
        attrs.append(f'data-email-subject="{html.escape(subject, quote=True)}"')
    return f'<a {" ".join(attrs)}>{html.escape(label)}</a>'
```

Usar el escape/helper que encaje con el estilo real del builder; no copiar literalmente si ya existe una utilidad equivalente.

3. En `render_footer()` sustituir el mailto antiguo por el trigger.

4. Cargar una sola vez:

```html
<script defer src="/assets/email-reveal.js?v=1"></script>
```

El owner del shell debe garantizar que aparece en todas las páginas V1 que renderizan un trigger. No crear una copia del runtime por página.

5. Regenerar:

```bash
python scripts/build-site-shell.py
python scripts/build-site-shell.py --check
```

6. Verificar que la regeneración no altera accidentalmente header, Explore, afiliación, newsletter, CSP o el resto del footer.

### B. `prensa.html`

Sustituir solo las CTAs email actuales por triggers `data-email-reveal`.

No tocar el contenido editorial de la página salvo el texto necesario para que el primer gesto sea comprensible.

Para la tarjeta que hoy imprime la dirección, usar algo como:

```html
<p>
  <a href="#contacto" data-email-reveal data-email-label-after="Abrir correo">
    Mostrar correo de contacto
  </a>
</p>
```

Para acciones con subject, mantener el asunto mediante `data-email-subject`.

No dejar una dirección escondida en `aria-label`, `title`, comentarios HTML o atributos alternativos: también son HTML scrapeable.

### C. Otras superficies

Después de regenerar el shell ejecutar:

```bash
python scripts/audit-public-email-exposure.py --strict
```

Cualquier finding es un owner que falta. No crear allowlist para conseguir verde salvo que exista una razón pública documentada que justifique explícitamente publicar el email estático.

## CI requerido antes de merge

Mínimo:

```bash
python tests/test-email-protection.py
python scripts/audit-public-email-exposure.py --strict
python scripts/build-site-shell.py --check
```

Añadir el test/gate al Required merge gate o al workflow transversal adecuado una vez la migración produzca 0 findings.

Además ejecutar:

- Pa11y baseline;
- Sitewide Reflow;
- CSP public shell;
- Runtime scoping;
- QA de Prensa;
- Lighthouse relevante.

## Browser QA mínimo

Desktop + 390px + 320px, teclado y pointer:

1. footer muestra «Mostrar correo» sin dirección en DOM inicial;
2. activación revela la dirección;
3. el enlace revelado tiene `mailto:` correcto;
4. foco queda en el enlace revelado;
5. segunda activación abre el handler de correo normal;
6. CTA «Solicitar entrevista» conserva su asunto;
7. CTA de reseña conserva su asunto;
8. con JS deshabilitado, footer lleva a `/prensa.html#contacto` y las CTAs de Prensa siguen llevando a `#contacto`;
9. 200 % zoom/text resize sin overflow;
10. ninguna petición de red se dispara al revelar el correo.

## Threat model / límites

Esta PR sí reduce:

- crawlers que extraen regex de emails;
- parsers HTML que decodifican entidades numéricas;
- harvesting masivo que no ejecuta interacción;
- exposición accidental repetida en cada footer.

Esta PR NO puede impedir:

- extracción por un navegador automatizado que haga click;
- extracción manual;
- emails obtenidos de Goodreads, redes, directorios, registros previos o data brokers;
- spam enviado a una dirección ya conocida;
- phishing dirigido por agentes humanos/IA.

Por eso el éxito se mide como **reducción de superficie de scraping web**, no como promesa de «cero spam».

## Opcionales posteriores, fuera de este merge

Solo si el spam sigue siendo alto después de desplegar y medir:

- alias público distinto que reenvíe al inbox real, para poder rotarlo sin cambiar la cuenta principal;
- filtros Gmail por patrones de phishing/agente falso;
- autenticación SPF/DKIM/DMARC del dominio si se pasa a correo `@davidportodiaz.com`;
- formulario de contacto server-side con honeypot/rate limit como alternativa, no como sustituto obligatorio del email visible;
- protección de Cloudflare si el dominio pasa por proxy y se valida que no rompe CSP/accesibilidad.

No introducir CAPTCHA/Turnstile solo para enseñar una dirección salvo evidencia de que la capa ligera es insuficiente.

## Definición de cierre

No marcar la PR como completa hasta que:

- `PUBLIC_STATIC_EMAIL_EXPOSURES=0`;
- footer migrado;
- Prensa migrada;
- subjects preservados;
- runtime cargado una sola vez;
- no-JS funcional;
- keyboard/screen-reader usable;
- `audit-public-email-exposure.py --strict` verde;
- `build-site-shell.py --check` verde;
- CI transversal verde;
- QA de navegador aprobado.

Taxonomía final esperada:

`DOCUMENTED=true · RUNTIME_IMPLEMENTED=true · STATIC_MARKUP_MIGRATED=true · CI_GUARD=true · MERGED_MAIN=false/true según estado · VERIFIED_LIVE=false hasta deploy/smoke`
