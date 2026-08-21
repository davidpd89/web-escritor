# Asistente web — despliegue y activación

Esta rama deja el código listo para revisión, pero **no activa producción**. La página permanece `noindex,nofollow` y el Worker falla cerrado mientras `ASSISTANT_ENABLED` no sea `true`.

## Arquitectura

- Frontend: `/asistente/`.
- Endpoint preferido: Worker Route same-origin `https://davidportodiaz.com/api/assistant*`.
- Recuperación local: intenta `/pagefind/pagefind.js`; si el índice aún no está desplegado, usa únicamente el allowlist local de `data/assistant-source-registry.json` para sugerir páginas.
- Recuperación remota: binding de instancia Cloudflare AI Search `ASSISTANT_SEARCH`, `retrieval_type=hybrid`, `fusion_method=rrf`, filtro previo `visibility=public`.
- Generación: binding Workers AI `AI`; modelo fijado por `ASSISTANT_MODEL` en servidor.
- Fuentes: cada chunk debe llevar metadata `source_id`; el Worker solo publica URLs resueltas desde el registry de la web.
- Rate limit: dos bindings, `SESSION_RATE_LIMITER` y `GLOBAL_RATE_LIMITER`. No se usa la IP como identidad primaria.

## Configuración mínima de Cloudflare

1. Crear/usar una instancia AI Search con búsqueda vectorial + keyword y RRF.
2. Definir custom metadata al menos `source_id` (text) y `visibility` (text). Los documentos de este asistente deben indexarse con `visibility=public`.
3. Crear una instancia binding llamada `ASSISTANT_SEARCH` y un Workers AI binding `AI`.
4. Crear dos Rate Limiting bindings. Ejemplo de arranque conservador: sesión 6/min y global 120/min. Los namespace IDs deben ser distintos.
5. Variables: `ASSISTANT_ENABLED=false`, `ASSISTANT_MODEL=<modelo Workers AI elegido>`, `ASSISTANT_MATCH_THRESHOLD=0.42`.
6. Publicar el Worker en staging y probar. Solo después, crear la route `/api/assistant*` sobre el dominio.
7. Activar `ASSISTANT_ENABLED=true` únicamente cuando los tests de recuperación y las pruebas manuales sean verdes.

## Gate de integración

Antes de quitar `noindex` y enlazar la página desde navegación/registry:

- ejecutar `python scripts/check-assistant-contract.py`;
- ejecutar `node tests/test-assistant-core.mjs`;
- verificar 403/409/413/415/429/502/503 y timeout;
- comprobar que un `source_id` inventado nunca genera un enlace;
- comprobar que una pregunta fuera del corpus se abstiene o cae a búsqueda local;
- confirmar que no hay payload logging de prompts/respuestas en AI Gateway;
- confirmar que no existe fallback de pago ni Unified Billing para esta ruta;
- integrar `/asistente/` en `data/content-registry.json`, `data/navigation.json` y sitemap solo al activar la funcionalidad.

## Deliberadamente fuera de esta PR

- No se despliega ningún binding ni secreto.
- No se activa el Worker.
- No se genera un índice Pagefind porque el repositorio todavía no tiene pipeline Pagefind; el cliente ya detecta el índice cuando exista y degrada sin romperse.
- No se modifica `main` ni se cambia el estado de otras PR.
