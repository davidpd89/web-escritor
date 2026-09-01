# Accesibilidad — contrato de unificación visual

Fecha: 2026-08-31
Estado: contrato preparado; implementación pendiente
Cadena: continúa después de `DISEÑO - Legal` (#287)

## Superficie

- `/accesibilidad/`

La ruta es pública e indexable y funciona como declaración de accesibilidad del sitio.

## Baseline verificado

La página actual:

- usa `v1-fonts`, tokens/base, shell y `v1-editorial.css`;
- reutiliza una apertura `.cuaderno-masthead` aunque no pertenece a Cuaderno;
- contiene al menos una clase semánticamente ajena (`samuel-narrow`) para limitar ancho;
- declara WCAG 2.1 AA como estándar aplicado y describe alcance verificado, limitaciones y canal de contacto;
- tiene canonical propio y WebPage JSON-LD.

La reutilización visual no es por sí misma un bug, pero la dependencia nominal de Cuaderno/Samuel dificulta ownership y puede provocar fugas futuras. Debe evaluarse si conviene un owner local mínimo o clases neutrales, sin duplicar todo `v1-editorial.css`.

## Dirección visual

**Declaración de accesibilidad / documento de cumplimiento**, no artículo de Cuaderno ni pieza promocional.

Debe transmitir transparencia, legibilidad y facilidad para localizar:

1. estándar aplicado;
2. alcance comprobado;
3. limitaciones conocidas;
4. método/fecha de evaluación cuando conste;
5. canal para reportar barreras;
6. compromisos o próximos pasos solo si ya existen en el contenido factual.

Azul/dorado únicamente como jerarquía/orientación. No usar decoración que compita con el texto.

## Preservar estrictamente

- todos los hechos y formulaciones sobre WCAG/conformidad;
- alcance, excepciones y limitaciones conocidas;
- fechas, método de revisión y contacto;
- canonical, robots y WebPage JSON-LD;
- headings y orden lógico;
- enlaces;
- skip link;
- lectura completa sin JS;
- shell y navegación.

No elevar el grado de conformidad, eliminar cautelas ni afirmar pruebas que no hayan ocurrido.

## Implementación esperada

Revisar si `.cuaderno-masthead` y `.samuel-narrow` deben sustituirse por clases neutrales/locales. Si se hace, mantener geometría y semántica y proteger por QA que no se alteren Cuaderno ni Samuel.

Revisar también:

- longitud de línea;
- jerarquía h1/h2;
- listas y enlaces;
- contraste;
- foco;
- estados de ancla;
- contacto;
- footer/cierre;
- impresión si aporta utilidad.

## QA requerido

La propia PR debe ser ejemplar en accesibilidad:

- Pa11y/WCAG2AA sin regresiones;
- teclado completo;
- skip link visible y funcional;
- focus visible;
- 200 % zoom;
- text spacing WCAG;
- 320/360/390, tablet y desktop;
- forced-colors/high-contrast smoke cuando sea viable;
- reduced motion sin efectos innecesarios;
- no-JS;
- cero overflow;
- links/emails largos.

Proteger por assertions el texto/estado factual de conformidad para impedir que un cambio visual lo modifique accidentalmente.

## Aislamiento

No alterar artículos/Cuaderno, Samuel, Legal ni `/ai/`.

## Cierre

Mantener Draft y sin merge. No cerrar técnicamente hasta tener QA de accesibilidad/reflow y revisión visual verdes. Revisión física final bajo `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.