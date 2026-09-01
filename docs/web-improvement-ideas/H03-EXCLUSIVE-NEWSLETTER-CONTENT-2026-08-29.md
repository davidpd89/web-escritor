# H.3 · Contenido exclusivo para newsletter

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Matriz intermedia:** `PILOTAR`  
**Decisión:** solo existe tarea cuando hay material exclusivo real, derechos claros y valor incremental para el suscriptor.  
**Naturaleza:** documentación; no crea lead magnet ni campaña.

## 1. Hipótesis original

Ofrecer un fragmento/adelanto exclusivo, no publicado en la web, como incentivo de suscripción.

#135 corrigió la lectura automática de “más exclusividad = más conversiones”: el contenido debe existir, poder publicarse por email y ser suficientemente valioso. No se inventa un regalo para completar un funnel.

## 2. Evolución

| Etapa | Estado | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Contenido solo para suscriptores. |
| Revisión | `CONDITIONAL` | Es decisión editorial/derechos, no feature técnica. |
| Matriz | `PILOTAR` | Probar solo con material real. |
| Autoridad final/JSON | `CONDITIONAL` | Rights gate + valor genuino. |
| Revalidación independiente | mantenido | No generar volumen ni promesas artificiales. |

## 3. Estado actual de `main`

La Home actualmente promete novedades y menciona “el primer capítulo de Samuel entre mundos gratis”, pero el propio `script.js` advierte que **no hay una automatización Brevo verificada que entregue ese capítulo** y por eso el copy de éxito no promete entrega automática.

Esto demuestra por qué H.3 no puede implementarse empezando por más promesas: primero hay que reconciliar oferta pública, rights y delivery real.

La existencia de `/fragmento/` como lectura web tampoco convierte ese contenido en “exclusivo”.

## 4. Trigger

H.3 solo se abre cuando:

- existe una pieza concreta;
- el autor/editorial puede distribuirla por este canal;
- se ha decidido si será exclusiva temporal o permanentemente;
- no canibaliza un lead magnet/fragmento ya existente sin razón;
- el journey de suscripción/entrega está probado;
- se puede mantener la promesa editorial.

## 5. Formatos razonables

- escena eliminada o comentario del autor con derechos claros;
- adelanto previo a publicación autorizado;
- nota de proceso de primera mano;
- material descargable con valor real.

No hace falta que sea un PDF ni que requiera otra landing. Email/web canónica pueden bastar.

## 6. Riesgos y anti-patrones

- prometer “exclusivo” y reutilizar contenido público;
- ofrecer texto sujeto a contrato/editorial sin permiso;
- generar contenido IA solo para llenar la recompensa;
- crear varias copias indexables del mismo fragmento;
- capturar email antes de tener el activo/delivery;
- confundir valor editorial con escasez artificial.

## 7. Definition of Done si se pilote

- [ ] activo real identificado;
- [ ] derechos verificados;
- [ ] copy exacto y no engañoso;
- [ ] DOI + entrega E2E probados;
- [ ] baja/privacidad correctas;
- [ ] no duplicación indexable innecesaria;
- [ ] métrica previa: signup/click/respuesta, no vanity;
- [ ] decisión posterior KEEP/CHANGE/STOP.

## 8. Relación con otras ideas

H.2 debe cerrar el journey antes; C.4 comparte rights/duplicación; H.1 determina preferencias si el activo es temático; I.4 puede medir de forma agregada sin otro tracker.

## 9. Trazabilidad #135

Banco original, revisión 108/108, matriz (`PILOTAR`), JSON final, autoridad final y revalidación independiente revisados. Ninguna pasada posterior elimina el trigger de derechos/valor.

## 10. Cierre

H.3 no es “crear contenido exclusivo”. Es **usar como incentivo una pieza que ya merece existir y que puede entregarse legítimamente**. Hasta entonces permanece `CONDITIONAL`.