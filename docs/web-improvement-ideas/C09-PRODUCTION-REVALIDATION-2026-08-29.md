# C.9 · Revalidación de producción — traducción/adaptación y captación internacional

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #184  
Estado: **DEFER · NO_REAL_TRANSLATION_SURFACE · RIGHTS_PROJECT_NOT_VERIFIED · NO_HREFLANG_YET · NO_LEAD_CAPTURE · NO_CODE**

## Veredicto

C.9 sigue correctamente diferida. No existe en producción una versión inglesa/otra lengua equivalente, no existe `/en/`, no hay `hreflang` en el árbol inspeccionado y no se ha localizado en Drive un proyecto/licencia de traducción de Manecillas que permita presentar una edición internacional como producto real.

No se debe crear página, formulario, metadata inglesa, `hreflang` ni promesa de edición internacional hasta que cambien esos hechos.

## Evidencia directa de `main`

### Home

`index.html` declara:

- `<html lang="es">`;
- canonical `https://davidportodiaz.com/`;
- `og:locale = es_ES`;
- `WebSite.inLanguage = es`;
- `WebPage.inLanguage = es`.

No hay alternate inglesa.

### Manecillas

`/las-manecillas-del-recuerdo/` declara:

- `<html lang="es">`;
- canonical español;
- `og:locale = es_ES`;
- `WebPage.inLanguage = es`.

No existe una entidad de edición traducida ni una URL alternativa real.

### Árbol y sitemap

Inspección directa:

- `/en/` devuelve 404 en la base;
- el árbol recursivo no contiene rutas `en/`;
- no aparecen anotaciones `hreflang` en el árbol inspeccionado;
- `sitemap.xml` contiene las URLs públicas españolas actuales y no declara alternates localizados.

Esto es coherente con un sitio monolingüe español; no es una carencia por sí misma.

## Evidencia de proyecto/derechos

Se realizaron búsquedas específicas en Drive por:

- Manecillas + traducción/derechos/inglés/licencia internacional;
- traducción de Manecillas;
- Monza + derechos de traducción/licencia/contrato.

No se recuperó un documento que demuestre simultáneamente:

- idioma seleccionado;
- derechos/licencia de traducción/adaptación;
- proyecto aprobado;
- traductor/editorial/owner;
- calendario o entrega comprometida.

Estado correcto: `RIGHTS_PROJECT_NOT_VERIFIED`.

Esto no significa que los derechos no existan; significa que esta revalidación no puede probarlos y, por tanto, no debe fabricar una superficie pública basada en ellos.

## Hreflang vigente

Google documenta `hreflang` para versiones reales de una página destinadas a distintas lenguas/regiones.

Reglas relevantes:

- cada versión debe listarse a sí misma y a las demás;
- las URLs alternate deben ser completas;
- las relaciones deben ser bidireccionales para que se interpreten correctamente;
- puede implementarse en HTML, headers o sitemap, pero no hay ventaja en mantener varias técnicas simultáneas;
- una página cuyo contenido principal no está traducido no se convierte en una versión lingüística sustancial por traducir solo plantilla/metadata.

Por tanto hoy:

`hreflang = NOT_APPLICABLE_YET`

No añadir `hreflang="en"` apuntando a una página española ni a un placeholder.

## Canonical futuro

Si aparece una traducción real, cada versión lingüística debe tener su URL real y canonical coherente. La versión inglesa no debe canonicalizarse a la española como si fuera un duplicado artificial si contiene una traducción sustancial destinada a usuarios ingleses.

La arquitectura exacta (`/en/`, subdominio u otra) debe decidirse cuando exista el proyecto, no antes.

## Captación internacional

No crear ahora:

- «English edition coming soon»;
- lista «notify me in English»;
- segmento Brevo internacional sin producto definido;
- formulario de interés por derechos/traducción presentado a lectores;
- fecha tentativa pública.

Un registro de interés solo sería legítimo cuando exista un objeto suficientemente concreto para explicar:

- idioma/edición;
- qué comunicación recibirá el usuario;
- base de consentimiento;
- owner del envío;
- posibilidad de baja;
- ausencia de promesas no confirmadas.

## Trigger de reapertura

```text
language selected
AND translation/adaptation rights verified
AND real project approved
AND translated content or committed production schedule exists
AND editorial/translation owner exists
AND canonical/hreflang architecture can be mapped
```

Después, y no antes, decidir si existe necesidad de captación previa.

## Qué NO hacer

- metadata inglesa sobre cuerpo español;
- `/en/` vacío;
- traducción automática masiva para cobertura SEO;
- página de «coming soon» indexable;
- `hreflang` unilateral o hacia inexistentes;
- canonical cruzado sin arquitectura real;
- oferta/ISBN/editorial/territorio inventados;
- prometer una fecha internacional;
- crear una edición `Book` que todavía no existe;
- añadir internacionalización solo para aparentar alcance global.

## DoD

- [x] Home inspeccionada directamente;
- [x] Manecillas inspeccionada directamente;
- [x] `/en/` comprobado directamente como ausente;
- [x] árbol recursivo revisado para rutas/hreflang;
- [x] sitemap inspeccionado directamente;
- [x] Drive buscado por proyecto/derechos/licencia;
- [x] guía Google `hreflang` vigente revalidada;
- [x] ausencia de evidencia tratada como `NOT_VERIFIED`, no como negación de derechos;
- [x] sin landing/formulario/metadata prematuros;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**DEFER · NO_REAL_TRANSLATION_SURFACE · RIGHTS_PROJECT_NOT_VERIFIED · NO_HREFLANG_YET · NO_LEAD_CAPTURE · NO_CODE**
