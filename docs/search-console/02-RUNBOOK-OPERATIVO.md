# 02 — Runbook operativo de Google Search Console

**Para:** davidportodiaz.com  
**Objetivo:** convertir datos de Search Console en decisiones repetibles y trazables.  
**Principio:** no cambiar la web por fluctuaciones sin contexto. Cada intervención debe vincularse a evidencia, hipótesis, cambio y medición posterior.

---

## 1. Severidad de señales

### P0 — actuar el mismo día

- Acción manual de Google.
- Problema de seguridad.
- Home o ficha de libro principal deja de estar indexada inesperadamente.
- Sitemap no se puede leer por fallo general.
- `robots.txt` bloquea por error una familia crítica.
- host/DNS/5xx grave visible en Crawl Stats.
- canonical elegida por Google apunta a otro dominio/URL inesperada para una página prioritaria.
- información sensible publicada accidentalmente y visible en Google → aplicar solución permanente + Removals si urge.

### P1 — investigar en 24–72 h

- caída fuerte y persistente de clics/impressions de una familia estratégica;
- incremento anómalo de URLs no indexadas por un motivo nuevo;
- grupo Core Web Vitals pasa a Poor en plantillas importantes;
- errores críticos de rich results a escala;
- sitemap procesado pero URLs prioritarias no se descubren/indexan;
- pérdida continuada de tráfico no-branded;
- impresiones GenAI desaparecen sin anomalía oficial/opt-out;
- propiedad social deja de estar conectada/verificada.

### P2 — optimización programada

- oportunidades CTR;
- consultas genéricas nuevas;
- contenidos que suben/bajan de forma gradual;
- internal linking mejorable;
- backlinks nuevos/interesantes;
- queries canibalizadas;
- dispositivos/países con patrón diferente;
- ideas de actualización de contenidos.

---

## 2. Rutina diaria — 3–5 minutos

No hace falta abrir 15 informes cada día. Revisar solo:

1. **Overview**
   - ¿alerta nueva?
   - ¿problema de seguridad/manual action?
   - ¿recomendación realmente urgente?
2. **Mensajes/notificaciones** de Search Console.
3. En periodos sensibles (lanzamiento/PR grande): **Performance 24h**.

### Días sensibles

Usar 24h durante:

- 3 de septiembre de 2026 y días siguientes por lanzamiento de Manecillas;
- publicación de una pieza que esperemos tenga interés inmediato;
- aparición en prensa relevante;
- después de cambio de dominio/CDN/routing;
- incidente técnico.

### No reaccionar a

- una hora sin impresiones;
- cambio de posición media de unas décimas;
- caída de un día sin confirmar tendencia/anomalías.

---

## 3. Rutina semanal — 30–45 minutos

Ideal: mismo día cada semana para comparabilidad.

### 3.1 Comprobar anomalías de Google

Antes de diagnosticar:

- revisar anotaciones del sistema;
- consultar página oficial Data anomalies;
- registrar cualquier periodo contaminado.

### 3.2 Search Performance: 7 días vs 7 días anteriores

Activar:

- Clicks;
- Impressions;
- CTR;
- Position solo como contexto.

Revisar:

1. Queries;
2. Pages;
3. Search appearance;
4. Devices;
5. Countries si aparece un cambio relevante.

### 3.3 Marca vs. sin marca

Si está disponible:

- clics branded;
- clics non-branded;
- impresiones non-branded;
- páginas que explican el crecimiento/descenso.

Pregunta semanal principal:

> ¿Estamos ampliando descubrimiento fuera de las personas que ya conocen a David o sus libros?

### 3.4 Revisar territorios

#### Obras

- Manecillas;
- Samuel;
- fragmentos;
- Noveris;
- clubes de lectura.

Preguntas:

- ¿qué obra recibe impresiones?
- ¿por título o por género/tema?
- ¿qué queries de lectura/fragmento aparecen?
- ¿hay consultas que piden algo que la ficha no responde?

#### Cuaderno

- artículos ganadores/perdedores;
- consultas nuevas;
- actualización potencial.

#### Herramientas

- herramientas con mayor entrada orgánica;
- nuevas queries problema/solución;
- páginas con muchas impresiones y CTR bajo.

#### Editoriales/Convocatorias/Recursos

- crecimiento genérico;
- queries de alta intención;
- oportunidades para nuevas fichas solo si existe contenido verificable real.

#### Recomendaciones

- qué temas lectores busca Google;
- posibles clusters legítimos.

### 3.5 Insights

Si disponible:

- Top content;
- Trending up;
- Trending down;
- top queries;
- trending queries;
- marca/genérico;
- fuentes adicionales.

Cada tarjeta debe terminar en una de tres decisiones:

- `NO ACTION` — ruido/explicable;
- `OBSERVE` — volver a mirar la próxima semana;
- `INVESTIGATE` — abrir análisis específico.

### 3.6 GenAI

Si el informe existe:

- impresiones semanales;
- páginas con mayor señal;
- nuevos contenidos que empiezan a aparecer;
- dispositivo/país solo si aporta decisión.

No comparar días afectados por anomalías conocidas de logging con periodos limpios.

### 3.7 Indexación rápida

No revisar todas las causas cada semana si no cambian. Mirar:

- nuevos errores;
- picos de exclusión;
- sitemap;
- prioridad URLs nuevas.

---

## 4. Rutina mensual — 90 minutos

Periodo base recomendado: últimos 28 días vs 28 anteriores y, cuando tenga sentido, comparación interanual/estacional.

### 4.1 Scorecard

Guardar:

- clicks total;
- impressions total;
- CTR total contextual;
- branded clicks;
- non-branded clicks;
- clicks por territorio;
- páginas indexadas esperadas;
- incidencias indexación;
- CWV status;
- GenAI impressions si existe;
- Discover clicks si existe;
- Google News clicks si existe;
- nuevas páginas con backlinks relevantes.

### 4.2 Top 10 cambios positivos

No limitarse a top absoluto. Calcular:

- páginas que más clics ganan;
- páginas que más impresiones ganan;
- queries que más clics ganan;
- queries nuevas con demanda significativa.

Para cada una:

- causa probable;
- si merece refuerzo interno;
- si hay cluster relacionado;
- si se debe actualizar o proteger.

### 4.3 Top 10 descensos

Para cada descenso:

1. ¿el dato está afectado por anomalía oficial?
2. ¿cambió la demanda o la página?
3. ¿cambió la query o el SERP?
4. ¿otra página propia está captando la misma query?
5. ¿cambió indexación/canónica?
6. ¿hay estacionalidad?
7. ¿el contenido quedó obsoleto?
8. ¿el descenso es relevante para negocio/editorial?

Solo crear tarea si hay una hipótesis accionable.

### 4.4 Oportunidades CTR

Proceso mensual:

- filtrar queries con muchas impresiones relativas a la propiedad;
- revisar posiciones competitivas;
- evaluar SERP;
- asociar query → URL;
- decidir cambio de snippet/contenido.

Registrar baseline antes de editar.

### 4.5 Canibalización

Buscar queries donde aparecen múltiples URLs propias.

No toda multi-URL es canibalización. Solo investigar si:

- dos páginas cumplen la misma intención;
- alternan de forma inestable;
- ninguna consolida señales;
- el contenido es redundante.

Posibles soluciones:

- diferenciar intención;
- consolidar;
- internal linking;
- canonical solo si realmente son duplicadas;
- redirect si se elimina una URL.

### 4.6 Internal links

Revisar informe Links:

- ¿las páginas prioritarias están entre las mejor conectadas?
- ¿alguna herramienta/artículo huérfano en crawl real?
- ¿la home/Obras/Cuaderno/Herramientas distribuyen autoridad?

### 4.7 Backlinks

Revisar:

- sitios nuevos;
- páginas enlazadas;
- anchor text inesperado;
- medios/editoriales/blogs que enlazan;
- recursos que atraen enlaces naturalmente.

No convertirlo en campaña de desautorización automática.

### 4.8 Core Web Vitals

- mobile;
- desktop;
- Poor groups;
- Needs improvement;
- plantillas comunes.

Cruzar con cambios de CSS/JS/imagen del mes.

### 4.9 Rich results

Solo informes presentes:

- errores;
- warnings;
- variación de items válidos;
- cambios de plantilla.

### 4.10 Crawl Stats / HTTPS / robots

Revisión mensual ligera:

- host status;
- 5xx;
- response times anómalos;
- HTTP indexado = 0 objetivo;
- robots sin errores.

---

## 5. Rutina trimestral — gobierno y estrategia

### 5.1 Usuarios y permisos

- propietarios;
- full users;
- restricted;
- accesos antiguos.

### 5.2 Asociaciones

- GA4 si existe;
- Ads si existe;
- Merchant Center solo si aplica;
- cualquier asociación antigua.

### 5.3 BigQuery

- export activo;
- último export correcto;
- coste;
- crecimiento tablas;
- política de expiración;
- queries/dashboards todavía útiles.

### 5.4 Platform properties

- Instagram conectada;
- TikTok conectada;
- revisar si han aparecido nuevos tipos soportados/cuentas canónicas;
- no duplicar perfiles no oficiales.

### 5.5 GenAI

- ¿control sigue incluido?
- ¿hay informe nuevo disponible?
- ¿qué territorios acumulan señal?
- ¿algún cambio en documentación oficial?

### 5.6 Arquitectura de contenido

Con 3 meses de datos:

- territorios que crecen;
- territorios estancados;
- contenido que trae lectores vs escritores;
- páginas que generan backlinks;
- consultas sin respuesta suficiente;
- contenido que nunca obtiene señales y quizá debe replantearse.

No borrar contenido únicamente porque tenga cero clics si cumple función editorial/navegacional.

---

## 6. Playbook de lanzamiento de contenido nuevo

### Antes de publicar

- URL final estable;
- canonical self;
- indexable si corresponde;
- title/description;
- H1;
- internal links;
- sitemap incluirá URL;
- structured data válido si procede;
- imagen adecuada;
- no queda `noindex`/staging accidental.

### Al publicar

1. desplegar;
2. comprobar HTTP 200;
3. comprobar canonical/robots;
4. confirmar sitemap actualizado;
5. añadir **anotación Search Console**;
6. URL Inspection live;
7. request indexing solo si es prioridad alta.

### +3 días

- ¿discovered/crawled/indexed?
- ¿primeras impressions?

### +7 días

- queries iniciales;
- page impressions;
- no optimizar demasiado pronto.

### +28 días

- evaluación real;
- cambio solo con evidencia suficiente.

---

## 7. Playbook específico: Las manecillas del recuerdo

### Antes/durante lanzamiento

- anotación: `RELEASE · Manecillas · publicación 03/09/2026`;
- inspeccionar ficha principal;
- inspeccionar fragmentos;
- confirmar sitemap;
- revisar Search 24h;
- revisar queries de título/autor;
- revisar branded vs non-branded;
- revisar Images si portada/visual obtiene señal;
- si aparece GenAI report, capturar baseline.

### A la semana

Comparar:

- título exacto;
- variaciones de título;
- autor + título;
- género/temas;
- página principal vs fragmentos;
- países/dispositivos solo si relevantes.

### A 28 días

Analizar si la ficha está captando:

1. demanda de marca;
2. descubrimiento por tema/género;
3. tráfico a fragmentos;
4. posibles snippets mejorables;
5. enlaces externos nuevos.

No añadir retailer/Offer porque Search Console muestre queries comerciales. La disponibilidad se actualiza solo con fuente comercial real y contrato editorial.

---

## 8. Playbook: actualización de artículo del Cuaderno

### Selección

Actualizar cuando existe una señal como:

- muchas impressions + contenido desactualizado;
- queries nuevas que el artículo podría responder legítimamente;
- pérdida sostenida sin anomalía;
- información factual que ya cambió;
- oportunidad de enlazado/cluster.

### Antes del cambio

Exportar:

- 28 días query/page;
- 3 meses si hay estacionalidad;
- anotación del cambio.

### Después

No cambiar URL salvo necesidad real.

Medir:

- impressions;
- clicks;
- queries;
- CTR;
- páginas relacionadas;
- backlinks si procede.

---

## 9. Playbook: herramienta gratuita

Para una herramienta, Search Console debe responder:

- ¿qué problema escribe el usuario?
- ¿la query usa el nombre de la herramienta o describe el problema?
- ¿qué términos informativos rodean el uso?
- ¿Google entiende la página como utilidad o como artículo?
- ¿qué otras herramientas aparecen para las mismas consultas?

### Oportunidades

- title orientado a tarea real;
- explicación breve indexable alrededor de la herramienta;
- ejemplos de uso;
- FAQs solo por utilidad humana, no por rich result;
- enlaces hacia herramientas relacionadas;
- no crear 5 herramientas casi iguales para una sola keyword.

---

## 10. Playbook: editoriales/convocatorias

Search Console es especialmente útil porque son datasets cambiantes.

### Monitorizar

- query + nombre editorial;
- `editoriales que aceptan manuscritos` y variaciones reales que aparezcan;
- concursos/premios con intención temporal;
- páginas que ganan tráfico por frescura;
- consultas donde falta una ficha.

### Regla editorial

No crear una ficha solo porque haya impressions potenciales. Debe existir:

- fuente verificable;
- información suficiente;
- utilidad real;
- mantenimiento posible.

---

## 11. Playbook de caída de tráfico

### Paso 1 — confirmar

- 7 días vs 7;
- 28 vs 28;
- clicks e impressions;
- Search type;
- branded/non-branded;
- territorio.

### Paso 2 — anomalías externas

- Data anomalies de Search Console;
- anotaciones del sistema;
- estacionalidad;
- cambio de demanda.

### Paso 3 — segmentar

- queries o pages;
- mobile/desktop;
- country;
- search appearance;
- web/images/video/news.

### Paso 4 — técnico

- indexación;
- canonical;
- robots;
- sitemap;
- status HTTP;
- CWV;
- manual/security;
- crawl.

### Paso 5 — contenido/SERP

- competencia;
- intención;
- snippet;
- obsolescencia;
- canibalización;
- cambios propios.

### Paso 6 — registrar

Abrir issue/PR con:

- fecha;
- magnitud;
- filtros;
- URLs;
- queries;
- hipótesis;
- evidencia;
- cambio propuesto;
- criterio de éxito.

---

## 12. Playbook de página no indexada

1. ¿debe indexarse según `content-registry`/política editorial?
2. URL Inspection versión indexada;
3. Live Test;
4. HTTP;
5. robots;
6. meta robots;
7. canonical;
8. sitemap;
9. enlaces internos;
10. contenido suficientemente distinto/útil;
11. motivo exacto en Page Indexing;
12. corregir causa;
13. request indexing si es estratégica;
14. validar a escala si afectaba múltiples URLs.

No «quitar noindex» si la exclusión era deliberada.

---

## 13. Playbook de canonical inesperada

Cuando Google elige otra canónica:

1. inspeccionar URL A y canónica elegida B;
2. comprobar `rel=canonical`;
3. redirects;
4. sitemap;
5. internal links;
6. similitud de contenido;
7. HTTP/HTTPS/trailing slash;
8. parámetros;
9. hreflang si algún día aplica;
10. señales externas.

Si A y B son realmente duplicadas, Google puede estar actuando correctamente. Corregir solo cuando la canónica elegida contradiga la arquitectura deseada.

---

## 14. Playbook de 5xx/host issue

1. Crawl Stats → Host status;
2. revisar tipo/tiempo;
3. identificar ejemplos;
4. GitHub/hosting/CDN/Worker logs;
5. uptime externo si existe;
6. corregir origen;
7. no bloquear Googlebot como «solución»;
8. comprobar recuperación;
9. anotar incidente.

---

## 15. Playbook de robots accidental

1. robots report;
2. versión obtenida por Google;
3. repo `robots.txt`;
4. entorno/CDN que lo sirve;
5. corregir;
6. pedir recrawl de robots si el impacto es crítico;
7. URL Inspection de páginas afectadas;
8. anotar.

---

## 16. Playbook de información sensible indexada

1. retirar/proteger contenido en origen;
2. decidir 404/410/password/noindex según caso;
3. no bloquear solo con robots;
4. usar Removals si hace falta desaparición rápida;
5. verificar todas las variantes de URL;
6. revisar cache/CDN/artefactos;
7. rotar secretos si hubo credenciales;
8. buscar copias internas;
9. documentar incidente;
10. comprobar desaparición.

---

## 17. Playbook de acción manual

1. congelar cambios SEO no relacionados;
2. leer alcance exacto;
3. exportar/evidenciar;
4. identificar causa y todas sus instancias;
5. corregir de raíz;
6. QA independiente;
7. solicitar reconsideración con explicación concreta;
8. no enviar solicitudes repetidas sin cambios;
9. monitorizar.

---

## 18. Playbook de security issue

1. tratar como incidente de seguridad, no SEO;
2. aislar/limpiar;
3. revisar integridad Git;
4. revisar Workers/hosting;
5. credenciales;
6. terceros/scripts;
7. URLs afectadas;
8. revisar Search Console;
9. solicitar revisión cuando esté resuelto;
10. posterior postmortem.

---

## 19. Criterios para crear una tarea SEO desde Search Console

Una observación debe convertirse en issue/PR solo si tiene al menos:

- **señal:** qué cambió;
- **relevancia:** por qué importa;
- **scope:** URL/query/territorio;
- **causa plausible:** no simple correlación;
- **acción:** cambio concreto;
- **riesgo:** qué se puede romper;
- **medición:** cuándo/sobre qué KPI revisar.

Plantilla:

```md
## Señal GSC
Propiedad:
Informe:
Periodo:
Filtros:
Cambio observado:

## Evidencia
URLs:
Queries:
Export/captura:
Anomalías oficiales descartadas:

## Hipótesis
...

## Cambio propuesto
...

## Riesgo
...

## QA
...

## Medición posterior
Fecha mínima de revisión:
KPI:
Criterio de éxito:
```

---

## 20. Umbrales: cómo evitar números arbitrarios

No fijar «si baja 10 % cambia title» para una web con volúmenes distintos por sección.

### Alertas absolutas

Sí existen eventos binarios:

- manual action > 0;
- security issue > 0;
- prioridad URL deja de indexarse;
- sitemap fetch error;
- HTTP indexed > 0 cuando no debería;
- canonical externa inesperada;
- 5xx generalizado.

### Alertas relativas

Para tráfico usar baseline propio:

- comparar 7d vs. 7d;
- confirmar en 28d;
- exigir persistencia;
- analizar por territorio;
- corregir por anomalías oficiales.

Una caída grande en una página de 2 clics no tiene el mismo peso que en el hub principal.

---

## 21. Registro mensual recomendado

Guardar una nota/archivo externo o BigQuery snapshot con:

```text
Mes:
Clicks total:
Impressions total:
Clicks branded:
Clicks non-branded:
Top gaining page:
Top losing page:
Top new query:
Indexed priority URLs:
Indexing incidents:
CWV poor groups:
GenAI impressions:
Discover clicks:
New meaningful backlink domains:
Annotations added:
Actions decided:
```

No hace falta versionar datos personales/query exhaustiva en el repositorio. El repo debe guardar metodología y cambios, no dumps indiscriminados de Search Console.

---

## 22. Orden de implantación en la cuenta real

### Sesión 1 — configuración

- Domain property;
- usuarios/permisos;
- sitemap;
- Overview;
- Page Indexing;
- URL Inspection priority set;
- manual/security;
- GenAI control si aparece;
- annotations convention.

### Sesión 2 — analítica

- Search Performance;
- brand/nonbrand;
- territorios;
- Insights;
- Discover/News si aparecen;
- GenAI si aparece;
- Links.

### Sesión 3 — técnica

- CWV;
- HTTPS;
- Crawl Stats;
- robots;
- rich results;
- Removals protocol.

### Sesión 4 — expansión/automatización

- BigQuery bulk export;
- API project;
- URL Inspection monitor;
- Instagram/TikTok platform properties;
- dashboard/alertas.

---

## 23. Qué debe recibir Claude si implementa automatización

Claude debe leer:

- `01-PLAN-MAESTRO.md`;
- `03-AUTOMATIZACION-API-BIGQUERY.md`;
- `data/content-registry.json`;
- sitemap builders/checkers existentes;
- scripts de editorial facts;
- política de secretos `.env.example`/CI.

No debe:

- commitear OAuth refresh tokens;
- commitear service-account JSON;
- escribir dumps de queries privados en el repositorio;
- modificar SEO automáticamente desde datos GSC;
- pedir indexación masiva sin necesidad;
- confundir API de inspección con live test.

La automatización debe ser **read/alert first**, cambios humanos después.