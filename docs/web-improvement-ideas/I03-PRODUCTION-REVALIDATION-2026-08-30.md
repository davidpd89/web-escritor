# I.3 · Revalidación de producción — scroll depth agregado

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `DEFER · READING_PROGRESS_IS_UI_ONLY · NO_EDITORIAL_DECISION_TRIGGER · NO_TRACKING_CHANGE`

## Estado real

`main` ya tiene una barra visual de progreso opt-in mediante `data-reading-progress`. Su listener calcula posición de scroll para actualizar UI local.

Eso no es analítica de scroll y no debe convertirse en tracking implícito. No se ha localizado un contrato vigente que envíe hitos 25/50/75/100 a GoatCounter por el mero hecho de que exista la barra.

## Por qué se mantiene DEFER

La profundidad es un proxy ambiguo. Un abandono al 40% puede significar que:

- la respuesta ya estaba resuelta;
- la persona encontró un enlace útil;
- el artículo era demasiado largo;
- la intención de búsqueda era distinta;
- el contenido posterior no interesaba;
- hubo una interrupción externa.

Sin una decisión escrita antes de medir, instrumentar scroll solo aumenta datos y riesgo de interpretar movimiento de pantalla como calidad editorial.

## Trigger exacto

Solo reabrir si existe una hipótesis accionable, por ejemplo:

> «Creemos que la sección X de esta familia concreta está demasiado abajo. Si la mayoría no alcanza X durante una ventana suficiente, la moveremos/resumiremos; si sí la alcanza, no cambiaremos la estructura.»

El experimento debe registrar antes:

- URLs/familia;
- pregunta;
- cambio esperado por resultado;
- ventana;
- muestra razonable;
- eventos mínimos;
- criterio de retirada;
- owner de la decisión.

## Implementación mínima si se activa

- Reutilizar GoatCounter existente.
- Alcance limitado a las URLs del experimento.
- Hitos discretos, una vez por carga/sesión cuando proceda.
- Payload sin email/contact ID/query/texto seleccionado.
- Actualizar la misma autoridad I.2/E.8 si cambia el tratamiento.
- Registrar resultado en el owner de experimentos.
- Retirar eventos cuando dejan de responder una pregunta vigente.

## No hacer

- No 25/50/75/100 sitewide por defecto.
- No Clarity/GA/Brevo Tracker para esta idea.
- No reutilizar el listener visual de `data-reading-progress` como tracking silencioso.
- No correlacionar con identidad de newsletter.
- No llamar «lectura completa» a 100% scroll.
- No mantener eventos eternamente sin decisión asociada.

## Cierre

I.3 permanece `DEFER`: primero pregunta editorial, después piloto mínimo. La existencia de progreso visual no cambia esa secuencia.