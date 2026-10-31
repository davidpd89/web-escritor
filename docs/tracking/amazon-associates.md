# Amazon Associates España — cuenta, tracking, reporting y cumplimiento

Fecha de revisión: **2026-09-07**  
PR owner: **#427 · `tracking/amazon-associates`**  
Estado: **RESEARCHED · SITE_COMPLIANCE_IMPLEMENTED_IN_MAIN · ACCOUNT_STATUS_NOT_VERIFIED · REPORTING_AND_TRACKING_PLAN_READY**

## Objetivo

Auditar la cuenta de Amazon Afiliados España asociada al tracking ID actualmente utilizado por la web (`davidporto-21`), verificar que el tráfico y los productos correctos se están atribuyendo, definir una estructura de tracking útil y medir rendimiento sin alterar la experiencia editorial ni incumplir las políticas vigentes.

Esta PR NO debe reabrir el trabajo de disclosure K.3 que ya está implementado en la web. Su owner es ahora la **cuenta externa + medición + calidad de enlaces**, no volver a añadir avisos visuales en cada página.

## Corrección de la premisa histórica del placeholder

El placeholder original decía:

> «sin añadir disclosure visible redundante fuera de las páginas legales»

Esa formulación está obsoleta/era incorrecta como regla general.

Amazon exige disclosure claro de la relación afiliada y el proyecto ya cerró ese gap mediante el trabajo K.3 posterior.

Estado actual del repo, a preservar:

- enlaces Amazon afiliados relevantes usan `rel="sponsored nofollow noopener noreferrer"`;
- el CTA global incluye disclosure visible `Afiliado` próximo al enlace;
- los enlaces Amazon específicos de Samuel/Noveris y Home dinámica recibieron cobertura equivalente;
- `aviso-legal.html` contiene la declaración de sitio requerida por el programa;
- el host matching de Amazon fue endurecido para no clasificar lookalikes como `amazon.evil.com`.

Coordinación histórica de cierre:

`#304 + #308 + #306 = cierre funcional K.3`

Por tanto #427 debe **auditar/preservar**, no duplicar disclosures ni retirarlos.

## Políticas de Amazon vigentes hoy

La página oficial de políticas de Amazon Afiliados España figura actualizada a **14 de abril de 2026**.

Fuentes oficiales:

- https://afiliados.amazon.es/help/operating/policies
- https://afiliados.amazon.es/help/operating/compare

Cambios relevantes de 2026 documentados por Amazon:

1. una compra debe cumplir el nuevo requisito temporal: el producto debe ser enviado/transmitido/descargado y pagado dentro del plazo aplicable de 180 días para resultar apto para comisión;
2. se amplió la exclusión de compras originadas en ciertos anuncios pagados/promocionados, con excepciones limitadas;
3. se ajustó el alcance de ciertas comisiones Onsite a la misma variante de ASIN de la página enlazada;
4. se actualizó la definición de `contenido original` para exigir comentario, análisis o transformación que aporte valor.

Aplicación práctica:

- no asumir que pedido = comisión final hasta envío/pago/aptitud;
- no atribuir conversiones de campañas pagadas sin comprobar sus reglas;
- enlazar al **ASIN/formato correcto**, especialmente Manecillas papel vs Kindle;
- la web ya tiene abundante contenido editorial original; no hace falta fabricar páginas de afiliación vacías.

## Identidad actual conocida

Tracking/store ID utilizado por el proyecto:

- `davidporto-21`

Esto procede de enlaces públicos del repo y de la declaración de afiliación vigente.

NO inferir desde Git:

- que la cuenta está activa;
- identidad fiscal aprobada;
- método de pago válido;
- balance;
- número de pedidos;
- ingresos;
- bloqueos/advertencias;
- mercados internacionales vinculados.

Todo eso requiere sesión autenticada.

## Qué son los Tracking IDs

Amazon confirma que los Tracking IDs:

- permanecen asociados al Affiliate ID principal;
- no son cuentas distintas;
- permiten separar rendimiento por web, estrategia o incluso enlaces;
- sus informes muestran clics, artículos pedidos/enviados, ingresos por artículos enviados y comisiones.

Fuentes oficiales:

- https://afiliados.amazon.es/help/node/topic/G5KVDATAT5RKBBBG
- https://afiliados.amazon.es/help/node/topic/GK5TZZ4AWML2QSLA

Amazon permite gestionar varios IDs bajo la misma cuenta; su ayuda indica un límite estándar de hasta 100 IDs por afiliado.

No necesitamos acercarnos remotamente a ese límite.

## Estrategia de Tracking IDs recomendada

NO crear un ID por enlace. Fragmentaría datos y complicaría mantenimiento.

Primero revisar qué IDs ya existen.

Si hoy todo usa `davidporto-21`, valorar separar únicamente superficies suficientemente distintas para responder preguntas reales.

Ejemplo conceptual — nombres finales deben ajustarse a lo que Amazon permita y a IDs disponibles:

- `davidporto-21` → baseline/global heredado;
- Home / CTA global;
- ficha `Las manecillas del recuerdo`;
- ficha `Samuel entre mundos`;
- Recomendaciones/editorial lists;
- newsletter solo si realmente incluye enlaces afiliados y las políticas/canal lo permiten.

No crear IDs para formatos que apenas generan clics hasta tener volumen suficiente.

### Pregunta que cada ID debe responder

Un ID solo merece existir si luego podemos preguntar algo como:

> ¿Los clics hacia Amazon desde la ficha de Manecillas convierten mejor que los del CTA global?

Si no hay una pregunta analítica clara, conservar el ID general.

## Productos y destinos canónicos a comprobar

### Las manecillas del recuerdo — papel

- ASIN `B0HHY9MYLM`
- URL directa: `https://www.amazon.es/dp/B0HHY9MYLM`
- shortlink usado por el proyecto: `https://amzn.to/4zW6Yeu`

### Las manecillas — Kindle

- ASIN `B0HHM71F46`
- URL directa: `https://www.amazon.es/dp/B0HHM71F46`
- shortlink del proyecto: `https://amzn.to/3SM4Oxu`

### Samuel entre mundos

- ASIN conocido en el proyecto: `B0GB6LGQFH`

No confundir:

- papel Manecillas con Kindle;
- Manecillas con Samuel;
- retailer no afiliado con Amazon;
- shortlink histórico con ASIN que haya cambiado.

## Auditoría de shortlinks y SiteStripe

Amazon mantiene **SiteStripe** para generar enlaces desde Amazon.es.

Fuente oficial:

- https://afiliados.amazon.es/help/node/topic/GJMMT7G4C8K4Y3AY

Claude debe:

1. abrir cada shortlink público actual;
2. registrar redirección final;
3. confirmar producto/ASIN/formato;
4. confirmar que el tracking esperado queda atribuido;
5. evitar sustituir enlaces por URLs copiadas manualmente que pierdan el tracking;
6. regenerar mediante herramienta oficial si un shortlink está roto/ambiguo.

Amazon señala que el Tracking ID no siempre tiene que permanecer visible en la URL final para que la sesión sea atribuida; no diagnosticar un enlace como roto solo porque el parámetro desaparezca tras la navegación.

Fuente:

- https://afiliados.amazon.es/help/node/topic/GF4RJEQNXSMR7SP3

## Reporting disponible actualmente

Amazon documenta, entre otros:

- ingresos;
- pedidos;
- artículos enviados;
- tipos de enlace;
- tendencias diarias;
- visitantes únicos;
- resúmenes de Tracking IDs;
- historial de pagos.

Fuentes:

- https://afiliados.amazon.es/welcome/topic/reports
- https://afiliados.amazon.es/help/node/topic/GMWAK55DQX8JEK7C

Los informes de artículos pedidos/recompensas se actualizan aproximadamente cada hora según la ayuda actual.

## Baseline que Claude debe capturar

No subir datos personales o financieros sensibles al repo.

Guardar de forma agregada:

- periodo auditado;
- Tracking IDs activos;
- clics;
- visitantes únicos si disponible;
- artículos pedidos;
- artículos enviados;
- conversión;
- comisiones agregadas por ID/superficie cuando sea útil;
- top productos comprados únicamente si no expone datos personales;
- errores/alertas de cuenta.

### Ventanas recomendadas

- últimos 30 días;
- últimos 90 días;
- desde lanzamiento de Manecillas, si la UI lo permite.

No comparar periodos con muy poco tráfico como si fueran estadísticamente significativos.

## Funnel web ↔ Amazon

El objetivo analítico es unir sin PII:

1. evento/clic en davidportodiaz.com;
2. superficie de origen;
3. Tracking ID Amazon;
4. clic/pedido/envío/comisión agregados.

No intentar identificar usuarios individuales entre nuestra analítica y Amazon.

Nuestra analítica local puede medir **clic saliente**, Amazon mide **resultado afiliado agregado**.

## UTM y enlaces afiliados

No añadir parámetros arbitrarios a URLs de Amazon si pueden romper el formato oficial/shortlink.

Para medir origen:

- preferir Tracking IDs Amazon;
- usar eventos internos en nuestra web antes de abandonar el sitio;
- UTM solo en URLs propias cuando aporte valor.

No convertir los enlaces Amazon en cadenas de parámetros no documentadas.

## OneLink / mercados internacionales

La ayuda de Amazon mantiene funciones para enlazar IDs de tienda y Tracking IDs predeterminados internacionales.

Fuente oficial:

- https://afiliados.amazon.es/help/node/topic/G9JHP7AM9XQZREQR

No activar mercados internacionales por checklist.

Primero revisar:

- origen real de audiencia;
- disponibilidad de libros por país;
- si el mismo ASIN/formato existe en la tienda destino;
- implicaciones fiscales/account setup.

Si casi todo el tráfico/comercio es España, mantener la configuración simple.

## Compliance sitewide — checklist de preservación

Claude debe comprobar en producción y repo:

- declaración legal de Afiliado Amazon presente;
- disclosure visible próximo a enlaces afiliados globales y específicos cubiertos por K.3;
- `rel=sponsored` en enlaces afiliados;
- no aplicar `sponsored` a Casa del Libro/retailers no afiliados;
- host allowlist real Amazon;
- links correctos por ASIN/formato;
- no precios Amazon hardcodeados salvo uso permitido/actualizado;
- no copiar estrellas/reviews/rankings dinámicos sin permiso/API aplicable;
- no afirmar disponibilidad/stock permanente;
- no ocultar disclosures.

## Privacidad y secretos

NO versionar:

- datos fiscales;
- cuenta bancaria;
- dirección privada;
- identificadores de pago;
- screenshots con balances si revelan información sensible;
- cookies/tokens/session IDs;
- credenciales.

Sí se puede versionar:

- `ACCOUNT_ACTIVE=true/false` tras comprobarlo;
- lista de Tracking IDs no sensibles si son públicos en enlaces;
- métricas agregadas si David desea conservarlas;
- incidencias y fecha de resolución.

## Secuencia exacta para Claude

### 1. Cuenta

Entrar en Amazon Afiliados España y registrar:

- account active/suspended/pending;
- sitios registrados, especialmente `davidportodiaz.com`;
- información fiscal/payment = `VERIFIED` sin copiar valores privados;
- warnings/policy notices.

### 2. Tracking IDs

- listar IDs actuales;
- identificar cuál usan los enlaces públicos;
- cerrar IDs inútiles solo si está claramente permitido y no destruye reporting necesario;
- crear pocos IDs nuevos únicamente si hay pregunta analítica real.

### 3. Enlaces

Auditar:

- Home/header;
- Manecillas papel;
- Manecillas Kindle;
- Samuel;
- Recomendaciones;
- cualquier otro `tag=davidporto-21` del repo.

Confirmar destino y formato.

### 4. Reporting

Capturar baseline 30/90 días y desde lanzamiento.

Clasificar:

- clicks sin pedidos;
- pedidos sin enviados aún;
- superficie con mejor señal;
- enlaces sin tráfico;
- productos inesperados.

### 5. Compliance

Revisar políticas vigentes 14/04/2026 y la implementación K.3 actual.

Si algo cambió en las políticas desde esa fecha, actualizar el runbook antes de tocar producción.

### 6. Optimización

Solo después de datos:

- mejorar placement/copy de enlaces que ya aportan al usuario;
- retirar enlaces muertos;
- separar IDs si hay volumen;
- no convertir la web en un affiliate site genérico.

### 7. QA final

- desktop/mobile;
- enlaces abren producto correcto;
- affiliate disclosures legibles;
- target/rel correctos;
- reportes reciben clics de prueba en ventana razonable sin hacer compras artificiales;
- no realizar autocompras para probar comisiones.

## Criterio de cierre

`ACCOUNT_STATUS_VERIFIED · WEBSITE_REGISTERED · TAX_PAYMENT_STATUS_VERIFIED_WITHOUT_SECRET_EXPOSURE · TRACKING_IDS_INVENTORIED · PRODUCT_LINKS_VERIFIED · REPORTING_BASELINE_CAPTURED · SITE_COMPLIANCE_REVALIDATED · K3_DISCLOSURE_PRESERVED · OPTIMIZATION_ACTIONS_DOCUMENTED · NO_POLICY_WARNING_UNRESOLVED`

Si existe bloqueo externo:

`EXTERNAL_ACCOUNT_BLOCKER_RECORDED`

## No hacer

- no quitar disclosure visible por considerarlo redundante;
- no usar autocompras/órdenes artificiales;
- no crear decenas de Tracking IDs;
- no publicar datos fiscales/ingresos privados sin necesidad;
- no asumir comisión por pedido antes de que sea apto;
- no mezclar ASINs/formats;
- no usar enlaces Amazon en publicidad pagada sin revisar las reglas actuales;
- no añadir precios/reseñas/ranking dinámico mediante scraping;
- no abrir otra cuenta de Afiliados por cada superficie.

## Fuentes oficiales consultadas 2026-09-07

- Políticas vigentes: https://afiliados.amazon.es/help/operating/policies
- Cambios 14/04/2026: https://afiliados.amazon.es/help/operating/compare
- Tracking IDs: https://afiliados.amazon.es/help/node/topic/GK5TZZ4AWML2QSLA
- Definiciones/reportes Tracking ID: https://afiliados.amazon.es/help/node/topic/G5KVDATAT5RKBBBG
- Reports: https://afiliados.amazon.es/welcome/topic/reports
- Uso de informes: https://afiliados.amazon.es/help/node/topic/GMWAK55DQX8JEK7C
- SiteStripe: https://afiliados.amazon.es/help/node/topic/GJMMT7G4C8K4Y3AY
- Tracking ID y URL: https://afiliados.amazon.es/help/node/topic/GF4RJEQNXSMR7SP3
- Varios sitios/IDs: https://afiliados.amazon.es/help/node/topic/GJDYPQZK6E37RLPU
