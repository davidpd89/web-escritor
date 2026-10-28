# Viajes literarios · piloto, QA, SEO y plan de aceptación

**Estado:** checklist de futura implementación, no ensayos realizados. Esta PR no debe activar workflows, Actions, cronjobs, despliegues, ni introducir URLs públicas.

## 1. Piloto editorial controlado

**Objetivo:** descubrir qué partes son fiables y útiles con poco contenido real, antes de diseñar un recopilador masivo.

**Caso A — Madrid (descubrimiento por ciudad).** Buscar el destino Madrid, mostrar Barrio de las Letras como área y librerías/bibliotecas de interés histórico confirmadas por sus instituciones. Validar que un barrio no se falsea como pin exacto, que cada lugar tiene su fuente y que se entiende la diferencia entre «sitio cultural» y «escenario de una novela».

**Caso B — París (destino internacional).** Seleccionar varias librerías y un escenario urbano de una obra documentada; contrastar fuentes locales, disponibilidad de foto, denominación francesa, dirección pública, precisión, autor, y que no se traduce una asociación turística en afirmación literaria.

**Caso C — Juego de tronos (descubrimiento por libro/saga).** Partir de la obra y diferenciar tres grupos: mundo imaginario, referencia de inspiración real documentada y escenarios de rodaje de la adaptación televisiva. Si no hay prueba de una relación, omitir el punto. La rama NO contiene una lista de ubicaciones inventadas ni afirmaciones sobre residencias del autor.

**Criterios de entrada por POI/relación:** nombre inequívoco, lugar geográfico delimitado, tipo de vínculo claro, una fuente verificable para ese vínculo, texto original, estado aprobado, última revisión, imagen legal o ficha sin imagen. Si falla, queda en borrador.

**Muestra sugerida:** 2–4 lugares curados por destino y al menos una relación obra-lugar compleja; volumen es deliberadamente pequeño para medir tasa de rechazo, tiempo de verificación y viabilidad. No generar una página de ciudad con contenido vacío para SEO.

## 2. Flujo de investigación asistida

1. Encargo editorial acotado: «Busca librerías históricas visitables en París», «identifica 5 referencias de X obra»; incluir prioridad de fuente primaria.
2. Asistente devuelve **candidatos**, URL verificable, frase que respalda exactamente la asociación, tipo de relación, dudas, localización y posible licencia de imagen. Nunca etiquetar automáticamente como verificado.
3. Separar deduplicación de lugar de deduplicación de evidencia: mismo POI y 4 novelas → una ficha POI y 4 vínculos con sus fuentes.
4. Humano valida con páginas originales, elimina alusiones débiles y comprueba derechos de imágenes; marca aprobado.
5. Futuro exportador recoge solo aprobados, valida integridad, genera snapshot estable y muestra diff del contenido añadido/retirado; nunca toma instrucciones de HTML de terceros.
6. Futura build publica HTML/JSON local con mapa y fichas, con sus propios gates.
7. Auditoría posterior comprueba accesibilidad, enlaces, atribuciones, precisión y mantenimiento.

## 3. QA de datos y calidad editorial (futuro)

- [ ] Esquema: tipos, IDs únicos, referencias FK existentes, slug único/estable, ISBN cuando proceda, URL HTTPS sin credenciales, fechas ISO reales.
- [ ] Coordenadas WGS84: lat entre -90 y 90, lon entre -180 y 180, precisión no exagerada, no lat=0/lon=0 como sustitución de desconocido; POI en destino correcto sin inferir ruta caminable.
- [ ] Tipo de relación obligatorio y coherente: rodaje ligado a adaptación, ambientación a obra, biografía a autor; no promocionar vínculos populares no demostrados.
- [ ] Rechazar publicación sin fuente concreta y revisión humana, incluso si el POI existe en OSM/Wikidata.
- [ ] No filtrar datos privados ni notas editoriales a export público: domicilios, tokens, correo interno, prompts, evidencias protegidas y campos auxiliares.
- [ ] Imágenes: licencia/autor/atribución comprobados, formato e integridad, tamaño responsive, alt original, ausencia de hotlink no permitido.
- [ ] Caducidades: avisar de visita/cierre/horario con datos antiguos; nunca mostrar precio/horario como vigente por defecto; enlazar fuente oficial.
- [ ] Verificar que snapshots repetidos generan bytes estables salvo cambio legítimo; control de borrados, redirecciones y huérfanos.
- [ ] Errores de proveedor: timeout, rate-limit 429, respuestas vacías y HTML inesperado no alteran publicados; el importador conserva último snapshot correcto.
- [ ] Uso responsable de fuentes: trazas de origen; licencias por dato; no copiar contenido largo, reseñas ni fotos sin derechos.

## 4. QA de interfaz y accesibilidad (futuro)

- [ ] Navegable por teclado y lector de pantalla, filtros con etiquetas reales, foco visible y recuento de resultados anunciado.
- [ ] Sin JS: fichas accesibles desde HTML indexable, mapa nunca como único modo de descubrir lugares.
- [ ] Móvil: controles no bloquean el scroll; filtros en viewport estrecho; fotos con aspect ratio y tamaños sin CLS.
- [ ] Mapa: atribución visible, popups accesibles, marcadores no se superponen de manera inmanejable, clustering contrastado; soporte reduccion de movimiento; fallback sin WebGL o con CSP estricta.
- [ ] CSP, scripts locales y dependencias en versión fija compatibles con estándares de la web actual; test de bloqueo de externos.
- [ ] Rendimiento: evaluar JS inicial, bytes de GeoJSON por destino, carga diferida del mapa, accesibilidad y LCP/CLS frente al baseline real de esta web.
- [ ] Filtros combinables por destino/libro/autor/tipo; manejar entidades relacionadas n:m, sin duplicar POIs. Búsqueda sin resultados comunica por qué.
- [ ] Usuarios nunca ven spoilers antes de activar contenido marcado.

## 5. QA SEO / integración

- [ ] Navegación, data/navigation.json y data/content-registry.json siguen siendo fuentes de verdad; no regenerar a mano páginas fuente generadas.
- [ ] Una URL canónica por destino y por lugar realmente distintos. Obras existentes redirigen a /recomendaciones/libros/<slug>/; no crear páginas duplicadas con mismo texto.
- [ ] Páginas sin contenido sustantivo/elementos en borrador no se publican; no indexar combinaciones arbitrarias de parámetros de facetas.
- [ ] Title y meta description originales con intención «qué ver literario en <ciudad>» o «lugares de <obra>» sin prometer ubicaciones falsas.
- [ ] JSON-LD de tipos verdaderos Schema.org (Place/TouristAttraction/Book/BreadcrumbList/CollectionPage según contexto); no fingir AggregateRating o Events sin datos.
- [ ] Sitemap/Pagefind/robots/canonicals y enlaces internos sin romper referencias actuales, incluyendo vínculo catálogo ↔ destino ↔ lugar ↔ ruta.
- [ ] Cambios nunca rompen /recomendaciones/, /cuaderno/ ni guías antiguas; CI/QA solo en PR futura autorizada, no aquí.
- [ ] Pinterest futuro: pin a ficha web propia, no salto directo Amazon; portada y texto con licencia y coherentes con la landing.

## 6. Métricas para decidir si se desarrolla

Medir tras ensayo editorial (no simuladas):
- % de candidatos descartados por ausencia de evidencia (calidad de descubrimiento).
- Minutos de trabajo para aprobar un POI y una asociación.
- % con fotos reutilizables, coordenada fiable y vínculo real con libro.
- % con libro ya presente en el catálogo; densidad de destinos.
- Riesgo de mantenimiento por horarios/cierres y cambios legales.
- Coste de consultas/hosting y tamaño/rendimiento de mapas.
- Una vez publicado: búsquedas internas por destino/obra, clics a fichas, retorno al catálogo, enlaces salientes y tráfico de Pinterest, sin inferir conversiones no medidas.

## 7. Definición de «listo para arrancar implementación»

- [ ] Propietario aprueba alcance y prioridades de contenido.
- [ ] Se elige arquitectura, librería de mapa, proveedor de tiles y política de licencias.
- [ ] Contrato Sheets/JSON versionado con mínimo un piloto real validado, sin registros inventados.
- [ ] Relación exacta con PR/ramas de recomendaciones revisada sobre main del momento.
- [ ] Lista concreta de gates e integración sin cron/publicador duplicado.
- [ ] Fuente externa permitida y coste/caducidad documentados por proveedor.
- [ ] Mock editorial con 3 casos y revisión de accesibilidad, sin confundir mock con contenido público.
- [ ] Solo entonces abrir **otra PR de implementación**, mantener esta de investigación como archivo de decisiones. Ningún merge automático.

## 8. Registro de decisiones y cuestiones abiertas (2026-10-21)

**Aprobadas como propuesta técnica provisional:** datos estáticos/versionados en web, Sheets como backoffice opcional, vínculo independiente POI↔obra↔autor, afirmaciones individuales respaldadas, libros enlazados con el catálogo existente, mapa opcional con fallback textual.

**A evaluar:** ubicación final del menú, país inicial, mapa y rutas en MVP, volumen de fichas a curar, terminología de relación, importación integrada o nueva, licencias y hosting cartográfico, datos de visitas y actualizaciones, estrategia Pinterest, nombres de tabs definitivos.

**Seguimiento de esta PR:** cada hallazgo nuevo se incorpora aquí o en 02-fuentes-y-repos.md con URL, fecha de consulta, qué valida, limitación y decisión. Evitar conclusiones solo en comentarios de chat.
