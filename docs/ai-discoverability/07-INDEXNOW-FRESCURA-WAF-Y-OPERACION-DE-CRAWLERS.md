# 07 — IndexNow, frescura, WAF y operación de crawlers

## 1. Problema que resolvemos

Una web puede tener el dato correcto en producción y aun así seguir apareciendo con un dato viejo en:

- cachés de buscadores;
- índices de búsqueda;
- snapshots de herramientas;
- respuestas de asistentes;
- snippets;
- resultados generativos.

Para una web con lanzamientos, eventos, convocatorias y datos editoriales, la **latencia de actualización** es parte de la calidad.

---

## 2. IndexNow

Microsoft conecta expresamente IndexNow con mantener contenido fresco para Search y experiencias de IA.

### Protocolo

Permite notificar URLs:

- añadidas;
- actualizadas;
- eliminadas.

La documentación permite hasta 10.000 URLs por POST, pero eso es un máximo técnico, no una invitación a reenviar todo el sitio.

### Endpoint recomendado

`https://api.indexnow.org/indexnow`

### Ownership

Requiere una key y un archivo público que demuestre control del host.

La opción recomendada por el protocolo es alojar:

`https://davidportodiaz.com/{KEY}.txt`

con la key como contenido.

### Seguridad

La key no es una credencial de acceso al sitio, pero no debe reutilizarse como ningún otro secreto.

---

## 3. Arquitectura propuesta en repo

### Archivos

```text
scripts/indexnow/
  build-changed-url-list.py
  submit-indexnow.py
  README.md

data/
  indexnow-state.json       # opcional, estado no sensible
```

La key real:

- GitHub Actions secret / Cloudflare secret;
- nunca commit.

El archivo de verificación público puede generarse en build desde una variable si el sistema de deploy lo permite, o mantenerse como artefacto público si la política de seguridad lo aprueba.

---

## 4. Cómo decidir qué URLs enviar

### Enviar

- nueva página indexable;
- cambio factual material;
- actualización sustancial de artículo;
- cambio de título/H1/metadata con impacto real;
- cambio de disponibilidad comercial;
- cambio de evento;
- convocatoria que abre/cierra;
- URL eliminada/410/redirect relevante;
- corrección factual crítica.

### No enviar

- cambio de espacio/format;
- recompilación sin cambio público;
- modificación de docs privadas;
- cambio de test;
- timestamp artificial;
- asset que no altera una URL de contenido salvo que exista razón específica.

---

## 5. Fuente de URLs cambiadas

La implementación ideal compara dos manifestaciones del **artefacto público**, no solo `git diff`.

### Por qué

Un cambio en:

- template;
- generator;
- source data;

puede alterar 20 páginas aunque el diff solo muestre un script.

### Propuesta

1. construir dist base;
2. construir dist head;
3. hash de HTML/text machine-readable público por URL;
4. detectar added/modified/deleted;
5. filtrar por indexability/content registry;
6. enviar lista.

---

## 6. No enviar noindex/gated

Antes de submission:

- consultar `content-registry`;
- excluir `noindex`, `internal`, `gated`, `deprecated`;
- excluir legales si no están destinados al índice;
- excluir staging;
- excluir archivos técnicos.

---

## 7. Momento del envío

**Después** de que producción sirva la nueva URL.

No notificar antes del deploy porque el crawler podría recuperar la versión vieja.

### Secuencia

```text
merge aprobado
→ deploy production
→ smoke origin
→ verify canonical/indexability
→ IndexNow changed URLs
→ observabilidad
```

---

## 8. Fallos de IndexNow

Interpretación del protocolo:

- `200`: recibido;
- `202`: recibido, validación de key pendiente;
- `400`: formato;
- `403`: key no válida/no accesible;
- `422`: host/URL/key incoherente;
- `429`: demasiadas peticiones.

### Regla

Un `200` **no significa indexación**. Solo recepción.

No reintentar agresivamente.

---

## 9. `lastmod`

Los sitemaps deben reflejar cambios materiales.

### No hacer

`lastmod = hoy` para todas las URLs en cada build.

### Sí

Derivar de:

- fecha editorial real;
- metadata de contenido;
- manifest histórico del artefacto;
- source file cuando exista autoridad fiable.

La frescura falsa degrada la señal.

---

## 10. HTTP freshness

Evaluar:

- ETag;
- Last-Modified;
- cache-control;
- CDN purge tras deploy;
- no servir HTML obsoleto por caches desalineadas.

### Especialmente para

- `/ai/`;
- `llms.txt`;
- `llms-full.txt`;
- home;
- Autor;
- fichas de libro;
- eventos;
- convocatorias.

---

## 11. Recrawl verification

Después de un cambio factual P0:

### Google

- URL Inspection cuando proceda;
- Search Console indexation.

### Bing

- URL Inspection;
- IndexNow;
- AI Performance con retraso razonable.

### ChatGPT/Claude/Perplexity

No hay una «request recrawl» pública equivalente documentada para cada uno.

Usar:

- acceso crawler permitido;
- sitemap/upstream indices;
- IndexNow donde aplique;
- benchmark posterior;
- logs.

---

## 12. Cloudflare/WAF

### Riesgo

`robots.txt: Allow` + `403` de WAF = de facto bloqueado.

### Comprobar

- Bot Fight Mode;
- Super Bot Fight Mode si existe;
- WAF custom rules;
- rate limiting;
- country rules;
- Browser Integrity;
- challenges;
- cache rules;
- Access.

### Nunca

Desactivar la protección global solo para que pase una IA.

---

## 13. Allowlisting por IP

### OpenAI

Fuente oficial dinámica:

- `https://openai.com/searchbot.json`
- feeds equivalentes del proveedor para otros agentes.

### Perplexity

- `https://www.perplexity.com/perplexitybot.json`
- `https://www.perplexity.com/perplexity-user.json`

### Anthropic

- `https://claude.com/crawling/bots.json`

### Regla

Validar:

- TLS;
- hostname exacto;
- JSON schema mínimo;
- `creationTime` si existe;
- CIDR parseable;
- tamaño razonable.

No aceptar un feed redirigido a host arbitrario.

---

## 14. Monitor de feeds IP

Futura tarea:

`scripts/ai-crawlers/sync-provider-ranges.py --check`

### Debe

- descargar únicamente hosts allowlisted;
- no modificar Cloudflare automáticamente por defecto;
- generar diff/report;
- avisar si cambia un prefijo;
- permitir revisión humana;
- no imprimir tokens de Cloudflare.

### Fase posterior

Solo con autorización explícita, un workflow podría aplicar una ruleset concreta mediante API.

---

## 15. Logs de crawlers

Necesitamos saber si llegan.

### Campos mínimos agregados

- fecha/hora truncada;
- UA clasificado;
- path;
- status;
- cache status;
- country opcional no necesario;
- latency.

### No guardar por defecto

- IP completa indefinidamente;
- query strings sensibles;
- cookies;
- headers de usuario.

### Métricas

- hits/día por crawler;
- 2xx/3xx/4xx/5xx;
- top paths;
- hit a sitemap;
- hit a `/ai/`/book page;
- bloqueos WAF.

---

## 16. Clasificación de User-Agent

Ejemplo interno:

```text
search-openai
user-openai
training-openai
search-claude
user-claude
training-claude
search-perplexity
user-perplexity
search-google
search-bing
search-apple
other
```

### Valor

No mezclar training traffic con search visibility.

---

## 17. Health check externo

Crear una prueba periódica que compruebe desde internet:

- `/robots.txt` 200;
- `/sitemap.xml` 200 XML;
- `/ai/` 200;
- `/llms.txt` 200 text;
- `/llms-full.txt` 200 text;
- home 200;
- Manecillas 200;
- Samuel 200.

Y:

- canonical esperado;
- noindex esperado/no inesperado;
- fecha/ISBN tokens críticos.

Esto detecta deploy drift.

---

## 18. Knowledge freshness SLA interno

### Hechos P0

- ISBN;
- publicación;
- editorial;
- retailer;
- evento cancelado;
- premio/atribución;
- contacto.

Objetivo: repo + production el mismo ciclo de publicación.

### Hechos P1

- bio;
- enlaces sociales;
- cobertura externa.

Objetivo: revisión razonable, no urgencia absoluta.

---

## 19. Stale fact register

Archivo interno propuesto:

`data/ai-stale-facts.json`

Ejemplo:

```json
{
  "factId": "samuel-publication-year",
  "canonical": "2025",
  "observations": [
    {
      "surface": "public-web-snapshot:/ai/",
      "observed": "2026",
      "observedAt": "2026-08-27",
      "status": "stale"
    }
  ]
}
```

No incluir prompts privados/PII.

---

## 20. Revisión después de deployment

### T+0

- origin;
- CDN;
- robots;
- sitemap;
- IndexNow.

### T+1–3 días

- Google/Bing inspection;
- crawler logs.

### T+7 días

- benchmark rápido;
- Bing AI Performance.

### T+28 días

- benchmark completo;
- Search Console GenAI;
- AI referrals;
- stale facts.

No esperar que todos los modelos paramétricos «olviden» instantáneamente un hecho aprendido históricamente.

---

## 21. Content deletion

Cuando una URL se elimina:

- 301 si hay reemplazo real;
- 410/404 cuando no;
- retirar del sitemap;
- notificar IndexNow;
- actualizar enlaces internos;
- no bloquearla en robots si necesitamos que el crawler vea el 404/410/noindex.

---

## 22. Recrawl no es ranking

IndexNow acelera el conocimiento del cambio; no garantiza:

- indexación;
- citación;
- posición;
- recomendación.

Su valor para este proyecto es **reducir el tiempo durante el que una IA puede encontrar un dato viejo**.

---

## 23. Acceptance criteria IndexNow

- [ ] key pública verificada;
- [ ] secret/config separado;
- [ ] script dry-run;
- [ ] solo URLs del host;
- [ ] solo public/indexable;
- [ ] diff de artefactos;
- [ ] batch <= 10k;
- [ ] retries con backoff;
- [ ] no spam/re-submit eterno;
- [ ] logs sin key;
- [ ] test 200/202/400/403/422/429;
- [ ] workflow post-deploy, no PR;
- [ ] documentación de rotación.

---

## 24. Acceptance criteria crawler/WAF

- [ ] OAI-SearchBot puede recuperar página crítica;
- [ ] Claude-SearchBot puede recuperar;
- [ ] Claude-User no bloqueado por WAF;
- [ ] PerplexityBot no bloqueado;
- [ ] Perplexity-User no bloqueado;
- [ ] Googlebot/Bingbot/Applebot normales;
- [ ] no se ha abierto una regla global insegura;
- [ ] feed IP dinámico documentado;
- [ ] logs clasifican search/user/training.
