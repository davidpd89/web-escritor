# I.5 · Revalidación de producción — minimización de datos

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`IMPLEMENT_AFTER_E8_OWNER · REVIEW_CONTRACT_READY · KNOWN_PRIVACY_DRIFT · NO_SECOND_REGISTRY`

## Estado real

- `main` todavía no contiene el registro de terceros que esta idea necesita como inventario factual.
- Ese owner ya está implementado y validado en la PR DRAFT #206 (E.8): registro de integraciones, estados de activación, CSP/disclosure y gate previo a activar proveedores opcionales.
- Por tanto I.5 no debe crear otro inventario ni un segundo checker.
- Existe además un drift factual ya detectado: `privacidad.html` describe una casilla de aceptación para el newsletter mientras los formularios generales/runtime inspeccionados no la muestran ni la validan. Ese desajuste sigue pendiente; no debe darse por corregido desde esta PR.

## Modelo de revisión

Cuando el owner de E.8 forme parte de la base efectiva, la revisión periódica debe reconciliar:

1. proveedor/capacidad;
2. finalidad;
3. datos enviados o almacenados;
4. superficie que lo activa;
5. estado real (`active`, `conditional`, `optional_disabled`, etc.);
6. retención/configuración relevante cuando sea verificable;
7. disclosure público aplicable;
8. decisión `KEEP / REDUCE / REMOVE / VERIFY`;
9. responsable y fecha de revisión.

## Cadencia

- revisión ordinaria anual;
- revisión extraordinaria cuando se añada un proveedor, se active una capacidad opcional, cambie una finalidad, cambie el formulario/consentimiento o aparezca un incidente/drift factual.

No hace falta una tarea cron de código para cumplirlo: es gobernanza sobre un owner existente.

## Guardrails

- no almacenar secretos, tokens o claves en el registro;
- no añadir PII para facilitar la auditoría;
- no convertir una integración `optional_disabled` en activa por documentación;
- no asumir configuración externa que no se haya verificado;
- no usar esta PR para corregir de forma destructiva HTML largo sin una edición segura y revisable.

## Cierre

I.5 sigue siendo válida, pero su implementación correcta es una revisión periódica sobre E.8, no otro sistema. El drift de privacidad/formulario es precisamente el tipo de incoherencia que esta revisión debe detectar y resolver en el owner adecuado.