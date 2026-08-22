# Asistente web — despliegue, UX y activación

La experiencia visible funciona en dos capas independientes:

1. **Conversación local gratuita**, activa siempre. Resuelve intenciones frecuentes con respuestas deterministas y enlaces canónicos de la web; para preguntas no cubiertas usa Pagefind cuando exista y, en último término, el registro local de fuentes.
2. **Respuesta ampliada remota**, opcional. Solo se consulta cuando la pregunta no tiene una respuesta local suficiente y cuando los dos kill switches (`remoteEnabled` en cliente y `ASSISTANT_ENABLED` en Worker) están activos.

El visitante no debe ver términos de infraestructura como Worker, AI Search, Turnstile, registry, protocolo, modo remoto o cuotas. Si una capa técnica falla, el producto debe degradar a conversación/búsqueda local con copy normal.

## UX canónica

- El widget está **cerrado por defecto**. Nunca autoabre el panel.
- Puede mostrar una pista no modal «¿Buscas algo? Pregúntame» una sola vez por sesión y ocultarla automáticamente.
- El iframe se crea únicamente después de una acción explícita del visitante.
- Panel de escritorio: máximo aproximado 378 × 520 px.
- Panel móvil: objetivo máximo 58dvh / 500 px; no debe convertirse en una hoja casi de pantalla completa.
- La UI es un chat: bienvenida, transcript de turnos, sugerencias, composer y fuentes dentro de cada respuesta.
- Enter envía; Shift+Enter crea salto de línea. Escape cierra el widget desde el embed.
- Las preguntas sugeridas se envían directamente y las sugerencias contextuales dependen solo del pathname.
- La página `/asistente/` se transforma con el mismo cliente a la misma experiencia conversacional para no mantener dos productos distintos.

## Conocimiento local

`assets/assistant-local-knowledge.mjs` contiene respuestas breves de baja volatilidad y solo devuelve `source_id`; nunca URLs. El frontend resuelve esos IDs contra `assets/assistant-source-registry.js`.

Cobertura mínima actual:

- visión general del sitio;
- obras y autor;
- Las manecillas del recuerdo + fragmentos + fecha de publicación;
- Samuel entre mundos + capítulo 1;
- Noveris;
- herramientas para escritores;
- editoriales y envío de manuscritos;
- convocatorias/concursos;
- recomendaciones y Cuaderno;
- prensa/contacto;
- eventos/firmas;
- premios/reconocimientos.

Las preguntas ambiguas sobre fragmentos generan una aclaración («¿cuál de los dos libros?») y mantienen únicamente ese pequeño contexto de conversación.

## Arquitectura remota

- Endpoint preferido: Worker Route same-origin `https://davidportodiaz.com/api/assistant*`.
- Recuperación remota: Cloudflare AI Search con búsqueda híbrida/RRF y allowlist pública.
- Generación: Workers AI, modelo fijado en servidor.
- Fuentes: cada chunk usa `source_id`; las URLs solo pueden proceder del registro canónico.
- Antiabuso: Turnstile + límites por sesión/IP/global + cuota exacta D1.
- La respuesta remota nunca es requisito para que el widget sea funcional.

## Configuración mínima de Cloudflare

1. Crear/usar una instancia AI Search con búsqueda vectorial + keyword y RRF.
2. Definir metadata `source_id`; activar `visibility=public` solo cuando la indexación real la incluya y el gate correspondiente sea verde.
3. Crear binding `ASSISTANT_SEARCH` y Workers AI binding `AI`.
4. Configurar `SESSION_RATE_LIMITER`, `IP_RATE_LIMITER` y `GLOBAL_RATE_LIMITER` con namespaces distintos.
5. Configurar D1 `ASSISTANT_QUOTA_DB` y aplicar `migrations/assistant-quota.sql`.
6. Guardar `TURNSTILE_SECRET_KEY` como secret, nunca en el repositorio.
7. Mantener `ASSISTANT_ENABLED=false` durante staging.
8. Probar retrieval, fuentes, cuotas, timeout y degradación antes de activar.

## Gate de integración

Antes de retirar `noindex` o activar la capa remota:

- `python scripts/check-assistant-contract.py`;
- `node tests/test-assistant-core.mjs`;
- `node tests/test-assistant-widget.mjs`;
- `python tests/test-assistant-widget-static.py`;
- verificar que el panel nunca se abre solo;
- comprobar 320/360/390 px y teclado virtual en móvil;
- comprobar teclado, Escape, foco y reduced motion;
- probar manualmente respuestas locales con la capa remota desactivada;
- verificar 403/409/413/415/429/5xx/timeout sin mostrar jerga técnica al visitante;
- comprobar que un `source_id` inventado nunca genera enlace;
- confirmar que no hay payload logging de prompts/respuestas;
- confirmar que no existe fallback de pago.

## Principio de producto

**El asistente puede degradarse; la conversación y la navegación de la web no.**
