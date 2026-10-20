# Prompt: automatizar libros, afiliación y Pinterest con fuentes verificadas

Copia el bloque siguiente en ChatGPT con búsqueda o investigación disponibles. Preparado el 20/10/2026; debe comprobarse la fecha real de ejecución. No necesita claves ni datos privados de Afiliados.

```text
Investiga cómo automatizar el catálogo de libros de davidportodiaz.com con la información vigente en la fecha real de esta investigación. Responde en español de España. Abre las fuentes que cites: una búsqueda o un fragmento de resultados no bastan. Prioriza documentación oficial y distingue dato confirmado, inferencia y dato que no puedes verificar. No prometas exactitud absoluta, acceso a una cuenta ni cobertura exhaustiva sin pruebas. Incluye fecha de consulta y URL directa junto a cada conclusión importante.

Objetivo: descubrir libros y novedades sin que el propietario tenga que buscarlos e introducirlos uno a uno en Drive; completar datos e imágenes con procedencia, clasificar, generar una descripción propia y audio Elvira una sola vez por cambio de texto; publicar fichas coherentes y alimentar el proceso de Pinterest existente. Reducir llamadas y tokens reutilizando datos estructurados, ISBN/ASIN y resultados ya verificados. La hoja de Drive es opcional.

Estado REAL que debes tomar como punto de partida:
- Web estática en GitHub Pages; repo C:\GIT\web-escritor, davidpd89/web-escritor. Una URL por obra: /recomendaciones/libros/<slug>/; categorías múltiples; perfiles de autor; filtros por tema, género, edad, fecha, formato, precio, descuento y valoración. Los filtros comerciales solo utilizan datos vigentes.
- Piloto Coraline de Neil Gaiman, ISBN-13 de referencia 9788498382372. Destinos Amazon.es verificados: tapa blanda 8498382378, tapa dura 847888579X, Kindle B08CYCPBZN y audiolibro B08CR4VJRT. Tag existente davidporto-21. No confundir precio de suscripción con precio de compra.
- Creators API: app creada, credenciales EU en GitHub Secrets, OAuth funciona. La consulta respondió HTTP 403, mensaje “Your account does not currently meet the eligibility requirements.”. La documentación oficial consultada el 20/10/2026 identifica AssociateNotEligible y exige diez ventas cualificadas en los treinta días anteriores. Revalida esto y la aceptación final del programa para España; no confundirlo con el alta inicial de tres ventas en 180 días. No sabemos el contador de ventas válidas de la cuenta; no inventarlo.
- Hay un adaptador de SearchItems y tarea diaria que produce candidatos para revisión. No cubre todas las editoriales ni todas las altas de Amazon; no enriquece ni publica automáticamente las fichas.
- Existe un importador de las pestañas del Drive y revisión editorial. No hay identidad de servicio Google conectada. No supongas que la hoja debe seguir siendo el centro del sistema.
- MP3 estáticos con Elvira y caché por hash de texto/voz. Los visitantes no consultan un proveedor TTS. Para capítulos o fragmentos de terceros hace falta verificar derechos de publicación y narración; “gratis para leer” no demuestra autorización para redistribuirlo.
- Precios y ofertas de Amazon aún NO están conectados: no proponer copiar precios a mano desde HTML como precios permanentes. Hay contrato de datos comerciales con fecha y caducidad, sin mostrar cifras inventadas. Las valoraciones de Goodreads deben tener fuente, fecha, número de votos y caducidad; no fingir que tenemos acceso a su API.
- Pinterest ya tiene un proceso en C:\GIT\RRSS_DavidPorto. Reutilizarlo después de inspeccionar sus instrucciones y herramientas pertinentes si tienes acceso. Si no lo tienes, especifica exactamente qué información local falta, sin fingir haberlo leído. No reconstruirlo por intuición ni publicar pines durante esta investigación.
- Recorrido obligatorio del pin: Pinterest → ficha de nuestra web → Amazon solo al pulsar el usuario. Cada pin apunta a la ficha canónica con UTM; varias categorías/variantes no duplican el libro. Portadas auténticas y edición correcta. Las imágenes de Pinterest deben tener una procedencia apta para ese uso y estar separadas del contenido obtenido de Amazon cuando sus condiciones lo exijan.

Investiga y concreta:
1. Requisitos actuales de Creators API en España; qué significa el error, qué se puede comprobar, cuándo procede contactar con soporte y qué alternativas oficiales siguen operativas mientras falta elegibilidad. No proponer compras propias ni estrategias de ventas artificiales.
2. SearchItems/GetItems/GetVariations: campos realmente disponibles para libros, paginación, cuotas, cobertura y límites. Determina si hay algún feed oficial que permita descubrir todas las novedades por editorial y fecha. Si no puedes demostrar exhaustividad, dilo y propone una cobertura medible.
3. Fuentes editoriales ONIX, RSS, APIs o catálogos autorizados; fuentes bibliográficas abiertas. Compara alternativas con y sin acceso a Amazon: España, español, ISBN, edición, fechas reales, portada y derechos, permisos, coste, estabilidad, actualización y cobertura. Diferencia publicación original, edición, disponibilidad y primera detección.
4. Formatos y afiliación: ASIN correcto por edición, parámetros que deben conservarse, atribución al cambiar de formato, duración de sesión y restricciones. Requisitos de identificación de afiliación: separar declaración general y claridad del enlace, con fuente oficial vigente. No garantizar comisiones por cada clic o compra.
5. Precios y descuentos: vía permitida de obtención, actualización/caducidad, moneda, precio de referencia, disponibilidad, suscripción y ofertas condicionadas. Nunca combinar el precio de un eBook con el formato de tapa dura para filtrar ni inferir una rebaja sin precio de referencia válido.
6. Goodreads: acceso oficial real hoy (API, widgets, licencias o permisos), posibilidad de mostrar/persistir puntuaciones con atribución y usarlas para filtrar. Separa promedio de obra y edición, número de votos, verificación y caducidad. No asumir que el antiguo endpoint API funciona ni recurrir a servicios no oficiales sin explicar origen, coste y condiciones.
7. Perfiles de autores desde Wikipedia/Wikidata y fuentes oficiales: datos biográficos contrastables, atribución/licencia aplicable al texto o imágenes, actualización y relación con nuestros libros. No copiar biografías completas, fabricar fotos ni inventar libros presentes en el catálogo.
8. Fragmentos: localizar muestras oficiales; verificar por separado lectura enlazada, alojamiento del texto y narración TTS. Diseñar audio estático bajo demanda editorial, sin regeneración diaria ni descarga al visitar una página. Si no hay autorización, mantener el enlace oficial.
9. Reutilización del proceso Pinterest existente: punto de entrada, datos por variante, imagen vertical, enlaces y UTM, idempotencia para no duplicar pines, programación, errores y seguimiento. La investigación no autoriza publicaciones.
10. Automatización barata: ingesta estructurada e incremental, claves ISBN/ASIN/autor, deduplicación de reediciones, historial de primera detección, caché compatible con las condiciones de cada fuente y caducidad de campos cambiantes. Usar IA solo donde haga falta redacción propia, clasificación o reconciliación; no pedirle cada día los datos ya verificados de todos los libros. Analiza también reutilizar el flujo local que abre ChatGPT, y distingue sus dependencias reales de una API programática. No presupongas acceso ni costes incluidos.

Entrega compacta y utilizable:
A. Resumen con lo confirmado, lo bloqueado y lo que requiere una decisión del propietario.
B. Tabla fuente → campos → cobertura → licencia/permisos → coste comprobado → frecuencia/caducidad → automatización posible.
C. Dos arquitecturas: una operativa sin Creators API y otra con Creators API; indicar qué se puede compartir entre ambas y cuándo Drive aporta algo.
D. Pipeline propuesto con pasos deterministas, uso mínimo de IA y revisión/publicación. JSON de ejemplo sin precios/valoraciones inventados, con procedencia por campo y fecha.
E. Plan por fases que reutilice los scripts/repositorios existentes, pruebas, errores, reintentos y métrica de cobertura. Separar acciones realizables ahora de las que requieren permisos, acceso, costes o aprobación.
F. Lista de fuentes oficiales abiertas y contradicciones encontradas. Si faltan datos de cuenta o acceso local, pedir solo esos datos concretos al final; nunca contraseñas, cookies o secretos.

Fuentes iniciales que debes abrir y revalidar:
https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
https://affiliate-program.amazon.com/creatorsapi/docs/en-us/troubleshooting/error-codes-and-messages
https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding/register-for-creators-api
https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/search-items
https://afiliados.amazon.es/help/operating/agreement
https://afiliados.amazon.es/help/operating/policies
https://afiliados.amazon.es/help/node/topic/G9SMD8TQHFJ7728F
https://www.goodreads.com/api
https://www.goodreads.com/about/terms
https://help.pinterest.com/es/business/article/rich-pins
https://developers.pinterest.com/
```
