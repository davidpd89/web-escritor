# 09 — Multimodal, social, agentes y comercio

## 1. Por qué este bloque existe

La recomendación en IA ya no ocurre solo desde texto web. Los productos modernos pueden recuperar:

- imágenes;
- vídeo;
- posts públicos;
- datos de producto;
- mapas/local;
- acciones dentro de una web;
- search APIs de terceros.

Por tanto, «visibilidad en IA» debe incluir cómo se representa la entidad fuera del HTML largo.

---

# 2. Imágenes

Google afirma que imágenes y vídeo relevantes pueden crear oportunidades adicionales de aparición en sus experiencias generativas.

## Activos prioritarios

### David

- retrato oficial;
- versiones de prensa autorizadas;
- nombre/autor en contexto cercano.

### Samuel

- portada oficial;
- mockups secundarios;
- imágenes de eventos;
- Noveris/recursos propios cuando sean canónicos.

### Manecillas

- portada oficial;
- material de prensa autorizado;
- mockups humanos;
- eventos/lanzamiento.

## Requisitos

- nombres de archivo descriptivos;
- alt útil;
- captions cuando añaden contexto;
- imagen de calidad;
- ancho/alto explícitos;
- OG/Twitter;
- ImageObject cuando semánticamente corresponda;
- no bloquear crawler de imagen sin querer.

## No hacer

- keyword stuffing en alt;
- presentar mockup generado como fotografía documental;
- usar imagen de portada no autorizada en high-res;
- meter hechos importantes solo en texto rasterizado.

---

# 3. Vídeo

## Por qué

- Search generativo puede incluir vídeo;
- Gemini usa información pública de YouTube;
- Meta AI/recommendation ecosystems explotan Reels;
- Grok puede usar X Search si hay vídeo/post público;
- los transcripts son fuentes textuales adicionales.

## Si se abre YouTube oficial

No crear el canal vacío solo por IA.

Publicar contenido con propósito:

- trailer/teaser editorial;
- explicación de Noveris;
- lectura breve autorizada;
- entrevista;
- proceso de escritura;
- charla de club;
- evento.

### Metadata

- título claro;
- David Porto Díaz;
- obra;
- descripción;
- URL canónica;
- capítulos si procede;
- subtítulos;
- transcript;
- thumbnail legible.

### Web

Crear página/embebido solo si aporta contexto. `VideoObject` únicamente para vídeos reales.

---

# 4. Instagram / Facebook / Threads

## Entidad

Mantener:

- mismo nombre;
- bio coherente;
- URL oficial;
- foto reconocible;
- obra actual;
- links actualizados.

## Contenido recomendable

Más útil que repetir CTA:

- fragmento comentado;
- objeto/tema de Manecillas;
- worldbuilding;
- proceso;
- evento;
- lector/club con permiso;
- detrás de escena;
- respuesta a pregunta frecuente real.

Meta ha indicado que sus sistemas de recomendaciones incrementan presencia de contenido original; eso refuerza evitar reposts mecánicos.

---

# 5. TikTok

TikTok puede construir demanda de marca y aportar material público que otros buscadores descubran.

## Estrategia

- original vertical;
- decir/escribir título y autor;
- subtítulos;
- contexto suficiente sin depender del audio;
- CTA hacia página canónica cuando tenga sentido;
- no hashtags masivos irrelevantes;
- comentarios como fuente de preguntas reales para contenido web.

## Medición

La PR #110 de Search Console documenta nuevas platform properties de Google para TikTok/Instagram si el rollout está habilitado.

---

# 6. X / Grok

No hay perfil X canónico registrado en el estado actual del proyecto.

### Decisión

No crear por obligación de «Grok SEO».

Si se abre por estrategia social real:

- nombre estable;
- web;
- posts originales;
- threads útiles;
- entidad/obras claras;
- no engagement bait.

xAI documenta X Search como herramienta de retrieval, por lo que una presencia X real puede convertirse en fuente para Grok. Eso no justifica un canal abandonado.

---

# 7. Pinterest

Ya existe perfil canónico.

### Potencial

- portadas;
- recursos visuales de escritura;
- tarjetas de herramientas;
- citas propias breves, no quote spam;
- mood/contexto de obra con derechos claros.

### Regla

Cada pin importante debe llegar a una página útil, no solo home.

---

# 8. LinkedIn

Útil para la faceta profesional:

- publicaciones;
- prensa;
- eventos;
- colaboración;
- ensayos sobre escritura/industria;
- hitos verificables.

Menos prioritario para recomendación directa de lectura juvenil, pero relevante para entidad autor y oportunidades profesionales.

---

# 9. Agent-friendly website

Google y OpenAI están documentando experiencias agénticas. Un browser agent puede interpretar:

- DOM;
- accessibility tree;
- screenshots;
- forms;
- botones.

## Tareas críticas del sitio

### «Encuentra el libro»

- navegación directa;
- heading inequívoco;
- canonical;
- libro/autor.

### «¿Dónde lo compro?»

- links etiquetados por retailer;
- external/sponsored semantics correctas;
- no botón «Comprar» sin destino real.

### «Descarga el press kit»

- recurso localizable;
- formatos;
- contacto.

### «Suscríbeme»

- label email;
- consentimiento;
- estado de error/éxito;
- DOI;
- no CAPTCHA imposible para agentes sin fallback humano.

### «Encuentra próximo evento»

- fechas `time`;
- dirección;
- estado;
- Event JSON-LD real.

### «Usa una herramienta»

- inputs accesibles;
- botón claro;
- output textual;
- privacidad.

---

# 10. Accesibilidad como infraestructura de agentes

La inversión existente en accesibilidad tiene doble retorno:

- personas;
- agentes que usan accessibility tree.

Priorizar:

- labels;
- landmarks;
- headings;
- focus;
- button vs link correcto;
- aria-expanded/controls;
- estados live;
- no div-clickable.

No añadir ARIA redundante para «IA».

---

# 11. Commerce: cuándo un libro entra en shopping AI

## Contexto

ChatGPT product discovery puede usar:

- merchant feeds ACP;
- información pública de producto;
- retailers.

Google AI puede usar Merchant Center cuando la entidad es merchant/product seller.

## Estado David

La web es principalmente de autor; no se ha establecido un checkout propio como merchant principal.

## Acción actual

### Samuel

Optimizar fuentes donde sí está vendido:

- editor;
- Amazon;
- Casa del Libro;
- metadatos consistentes;
- portada;
- ISBN;
- reseñas auténticas.

### Manecillas

No crear retailer hasta URL verificada.

## Si en el futuro hay tienda directa

Entonces evaluar:

- Product/Offer reales;
- Merchant Center;
- OpenAI product feeds/ACP;
- inventario;
- precio;
- shipping/returns;
- checkout agentic;
- política comercial.

No antes.

---

# 12. ChatGPT product feeds / ads

Distinguir:

### Organic product discovery

Puede usar ACP + web + retail sources.

### Ads product feeds

Los feeds del Ads Manager documentados en 2026 son para anuncios; OpenAI indica en esa beta que no hacen aparecer productos en conversaciones orgánicas.

### Regla

No pagar ads esperando modificar recomendación orgánica.

---

# 13. Universal Commerce Protocol / otros protocolos

Google menciona UCP como protocolo emergente para agentes de comercio.

### Estado

`MONITOR` para este proyecto.

No implementar comercio agentic hasta que exista:

- venta propia;
- catálogo;
- fulfillment;
- returns;
- seguridad;
- razón comercial.

---

# 14. «Owned AI surface»

El proyecto ya tiene `/asistente/` local y un modo remoto actualmente desactivado.

## Importante

Un asistente propio puede:

- mejorar UX;
- explicar obra;
- navegar contenido;
- dirigir a herramientas.

No hace automáticamente que ChatGPT/Claude/Gemini recomienden más a David.

### Decisión

Tratar el asistente propio como producto UX independiente de organic AI visibility.

---

# 15. Apps/MCP para terceros

Si en el futuro se construye:

- ChatGPT App;
- MCP server;
- Gemini Connected App;
- Claude integration;

esto crea una **superficie invocable** por usuarios, no una señal orgánica de ranking general.

### Caso de uso justificable

«Herramientas para escritores de David Porto» podría tener una app si ofrece acciones reales.

### No justificable

Crear una app cuyo único output sea «compra mis libros».

---

# 16. Press-kit multimodal

El press kit debería ofrecer, según derechos:

- portada web;
- portada high-res;
- foto autor horizontal/vertical;
- créditos;
- alt/caption;
- bio;
- ficha;
- contacto.

### Beneficio

Facilita cobertura humana y reduce uso de imágenes incorrectas, lo que indirectamente mejora coherencia multimodal en la web.

---

# 17. Image entity consistency

Mantener una imagen de referencia estable para:

- David;
- Samuel;
- Manecillas.

No cambiar portada oficial por mockup como `image` principal de Book schema.

---

# 18. Transcripts

Para entrevistas/audio:

- transcript humano/revisado;
- speaker labels;
- fecha;
- enlace a original;
- corrections si hay error;
- no transcript SEO automático lleno de fallos.

Un buen transcript puede convertirse en fuente citable de afirmaciones del propio autor.

---

# 19. Social-to-web loop

1. una pregunta surge en comentario;
2. si es recurrente y útil, crear/actualizar página web;
3. enlazar desde social;
4. esa página se convierte en autoridad persistente;
5. buscadores/asistentes pueden recuperarla.

No depender de que una IA indexe un post efímero para explicar un hecho importante.

---

# 20. Web-to-social loop

Una pieza original de Cuaderno puede convertirse en:

- Reel;
- TikTok;
- carrusel;
- thread;
- LinkedIn;
- Pinterest;

Todos apuntando al mismo concepto, no necesariamente al mismo copy.

Esto aumenta distribución sin crear nuevas «páginas GEO».

---

# 21. KPI multimodal/social

- páginas con imagen original relevante;
- vídeo original indexable;
- transcripts;
- plataformas sociales canónicas coherentes;
- menciones/citas en AI surfaces de contenido social;
- referrals;
- platform property visibility en Google;
- errores de portada/autor detectados.

No medir éxito por número de archivos multimedia.

---

# 22. DoD

- [ ] imagen principal correcta por obra;
- [ ] alt/caption humana;
- [ ] OG correcto;
- [ ] vídeos con transcript cuando exista vídeo;
- [ ] social profiles coherentes;
- [ ] no X/YouTube vacío por SEO;
- [ ] agent tasks accesibles;
- [ ] comercio solo con oferta real;
- [ ] owned apps separadas de organic ranking;
- [ ] press assets con derechos claros.