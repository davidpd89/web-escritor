# Lectores beta — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de Asistente.

La familia es `noindex`, pero forma parte del ecosistema real del Autor y contiene un flujo funcional de envío. Debe revisarse por experiencia real, no ignorarse por no estar indexada.

Mantener Draft y no mergear fuera de orden.

## Superficies

- `/lectores-beta/`
- `/lectores-beta/enviar-manuscrito/`

Reconciliar robots/canonical y endpoints reales antes de modificar producción.

## Objetivo

Unificar el programa de Lectores beta y el envío de manuscrito con el sistema editorial azul/negro/dorado, preservando el carácter privado/controlado del flujo.

No presentar el programa como una campaña pública abierta si el estado real no lo permite. El diseño debe diferenciar claramente información, requisitos, privacidad, estado del programa y acción disponible.

## Dirección visual

### Página del programa

- dossier breve de participación, no landing de captación agresiva;
- jerarquía clara entre qué es, para quién, cómo funciona, qué se espera y privacidad;
- estado actual del programa visible y textual;
- azul/dorado para jerarquía/rails/reglas, cuerpo predominantemente neutro;
- evitar cards repetidas si la información puede funcionar como ledger/secuencia.

### Envío de manuscrito

- formulario como tarea principal;
- labels e instrucciones compactas y legibles;
- privacidad/consentimiento visible antes de enviar;
- validación/error/success accesibles y no dependientes solo de color;
- file input, límites/tipos y cualquier condición contractual deben permanecer claros;
- no usar Yellowtail en labels, errores, consentimiento o datos de archivo.

## Preservar estrictamente

- `noindex` de ambas rutas cuando corresponda;
- estado real abierto/cerrado/invitación si existe;
- copy factual sobre participación;
- privacidad y consentimiento;
- labels/aria/autocomplete;
- límites/tipos de archivo;
- endpoints y data-* del formulario;
- estados de validación/envío/error/success;
- protección anti-spam/CSP si existe;
- navegación desde/hacia Autor;
- analytics existentes;
- funcionamiento sin JavaScript donde exista fallback.

No afirmar que un envío real externo funciona si no se ha probado. No reabrir el programa ni cambiar su disponibilidad dentro de una PR visual.

## QA requerido

Contrato browser de las dos rutas y autoridad funcional existente.

Cobertura:

- 1440/1280;
- 1024/768;
- 430/390/360/320;
- seams reales;
- zoom 200 %;
- text spacing;
- teclado/focus;
- teclado móvil/safe areas en revisión física;
- cero overflow.

Estados reproducibles:

- formulario vacío;
- errores de validación;
- focus en controles;
- archivo/selección si puede probarse con fixture seguro;
- estado de envío simulado/local si el proyecto ya dispone de fixture;
- success solo si puede reproducirse sin afirmar un E2E externo inexistente.

## Aislamiento

Verificar que estilos beta no se filtren a Autor, Asistente ni herramientas.

## Revisión humana

Probar recorrido completo y especialmente:

- claridad del estado del programa;
- confianza antes de adjuntar un manuscrito;
- privacidad visible;
- formulario con teclado móvil;
- mensajes de error;
- retorno/navegación.

Seguir `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Definition of Done

- ambas rutas coherentes;
- `noindex`/estado/privacidad preservados;
- formulario accesible y funcional;
- ningún falso PASS de backend/E2E;
- responsive/zoom/text-spacing/teclado verdes;
- Autor/otras familias aisladas;
- evidencia revisada;
- CI verde;
- Draft y sin merge hasta revisión física.
