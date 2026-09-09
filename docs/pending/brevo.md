# Brevo — newsletter, entregabilidad, automatizaciones y diseño

Fecha de investigación: **2026-09-07**  
PR owner: **#400 · `tracking/brevo`**  
Estado: **WELCOME_AUTOMATION_FIXED_FOR_REAL · LECTORES_BETA_AUTOMATION_BUILT_INACTIVE · DOMAIN_AUTH_STILL_PENDING**

## Cierre parcial (2026-09-09) — hallazgo crítico y corrección real

**Contexto del error previo**: en una sesión anterior (08-09) se "arregló" el remitente y el contenido de tres plantillas en la biblioteca de Plantillas (`Bienvenida_Samuel_Email1/2/3`, IDs #2/#3/#4) creyendo que eran las que usaba la automatización de bienvenida. El usuario reportó en vivo que seguía viendo el email roto (bienvenida a Noveris, sin Manecillas, remitente `samuelentremundos@gmail.com`). Al investigar se descubrió que **cada paso "Enviar un email" de una automatización en Brevo tiene su propia plantilla interna, independiente de la biblioteca de Plantillas** (aunque comparten el mismo editor HTML). Las plantillas #2/#3/#4 editadas nunca estuvieron enlazadas a la automatización real — son copias huérfanas sin usar. Las plantillas realmente enviadas por la automatización activa (`Bienvenida newsletter — Lectores web`, automatización #2) son las #6 (paso #3, email de bienvenida), #7 (paso #5) y #8 (paso #7).

### Arreglado de verdad, en las plantillas #6/#7/#8 (las que sí se envían)

- **Email 1 (plantilla #6)**: contenido reescrito con una rama condicional — si `contact.NOVERIS` está definido (el lector hizo el test de personalidad de Noveris), recibe su resultado personalizado como antes; si no (la mayoría — alta desde home/explore/cuaderno/manecillas/fragmento), recibe una bienvenida genérica que menciona *Las manecillas del recuerdo* (con CTA de compra) y *Samuel entre mundos*. Remitente corregido a `David Porto Díaz <davidpd89@gmail.com>` (el remitente `davidportodiaz@gmail.com` que se había asumido **no existe como remitente verificado en Brevo** — los dos únicos verificados son `davidpd89@gmail.com` y `samuelentremundos@gmail.com`). "Responder a" personalizado corregido a la misma dirección (antes apuntaba también a `samuelentremundos@gmail.com`).
- **Email 2 (plantilla #7, "El mundo de Noveris")**: contenido de catálogo de fondo, correcto tal cual — solo remitente + texto de vista previa (no existía) corregidos.
- **Email 3 (plantilla #8, "Si quieres saber cómo termina")**: pitch de compra de Samuel con reseña real de Goodreads, correcto tal cual — mismo arreglo de remitente + vista previa.
- **DOI/confirmación de suscripción** (plantilla #9, transaccional, llamada directamente por el worker): ya no promete "el primer capítulo de Samuel entre mundos" a todo el mundo — ahora es genérico ("novedades de David Porto Díaz"). El remitente de este email YA estaba correcto en los envíos reales (`davidpd89@...brevosend.com`, confirmado en los logs transaccionales) — el worker lo fuerza directamente en la llamada a la API, así que el campo de remitente de la plantilla es en la práctica decorativo para este caso concreto.

### Lectores beta — automatización nueva, construida pero inactiva

No existía ninguna automatización para la lista `Lectores beta - #6`; cualquiera que se apuntara no recibía ningún email de bienvenida. Se creó **"Bienvenida — Lectores beta"** (automatización #6), duplicando la ya arreglada #2 y sustituyendo: la lista disparadora por `Lectores beta - #6`, y el único paso de email por un contenido dedicado (manuscritos sin publicar, sin calendario fijo, sin obligación, misma redacción que ya usa `/lectores-beta` en la web). **Queda guardada pero `Inactivo`** — activar una automatización que dispara envíos automáticos futuros es una acción que requiere el visto bueno explícito del autor; no se ha activado.

### Sin resolver / a decisión del autor

- Las plantillas huérfanas #1–#4 y #9 originales (visibles en Plantillas como "Bienvenida_Samuel_EmailN" y "Nueva plantilla") siguen existiendo sin usar. Inofensivas pero confusas. Borrarlas requiere confirmación.
- `davidportodiaz@gmail.com` no es un remitente verificado en Brevo; si el autor lo prefiere sobre `davidpd89@gmail.com`, hay que añadirlo y verificarlo en Brevo primero.
- Activar la automatización de Lectores beta.
- El resto del runbook original de abajo (autenticación de dominio DKIM/DMARC, arquitectura de contactos, QA de clientes de email, etc.) sigue sin ejecutar.

## Objetivo

Cerrar Brevo de extremo a extremo para que la newsletter de `davidportodiaz.com` tenga:

- captación coherente desde todas las superficies;
- double opt-in real;
- una arquitectura de contactos limpia;
- dominio autenticado y buena entregabilidad;
- plantillas coherentes con la web;
- automatizaciones útiles, no ruido;
- bajas/suppressions correctas;
- métricas interpretadas con criterio;
- QA real en clientes y dispositivos.

La decisión de producto sigue siendo: **NO añadir un checkbox visible de consentimiento a la newsletter**. El consentimiento se articula mediante el envío voluntario del email, el texto informativo visible y el double opt-in.

## Estado actual de la integración web

La web usa formularios propios y un worker/backend; no conviene sustituirlos a ciegas por formularios embebidos de Brevo.

`assets/newsletter-popup.js` confirma actualmente:

- el popup envía `source: "popup"`;
- espera `state === "pending_confirmation"`;
- muestra `Revisa tu correo` tras el alta pendiente;
- usa honeypot;
- comparte el flujo común `postNewsletter(...)`;
- solo se activa en familias concretas del sitio;
- no marca al usuario como suscrito en el momento de enviar el formulario.

Antes de tocar listas/segmentos, Claude debe enumerar **todas** las fuentes reales que salen del repo y del worker: Home, Explorar, Manecillas, Cuaderno, popup y cualquier otra. No asumir nombres.

## Arquitectura recomendada de contactos

Evitar una lista distinta por cada formulario si eso solo duplica estado. Preferencia:

- una lista maestra de newsletter confirmada;
- atributos consistentes para origen/interés;
- segmentos dinámicos para campañas concretas.

Campos a comprobar/crear solo si son realmente útiles:

- `SOURCE` o equivalente: superficie de adquisición;
- `INTEREST` o equivalente solo si existe una taxonomía real;
- fecha de alta/confirmación si Brevo ya la expone o si el worker la guarda correctamente;
- estado DOI confirmado;
- idioma solo si se utilizará de verdad.

No guardar en atributos de marketing información sensible ni texto libre innecesario.

## Double opt-in

Brevo recomienda double opt-in para formularios. En formularios creados dentro de Brevo, la plataforma añade automáticamente el atributo `DOUBLE_OPT-IN`; en nuestro caso el formulario es externo, por lo que **no hay que asumir que ese atributo exista o sea fiable**.

La sesión autenticada debe comprobar el flujo exacto actual:

1. usuario introduce un email nuevo en la web;
2. worker recibe la petición y aplica validación/honeypot/rate limit;
3. Brevo crea o actualiza el contacto como pendiente;
4. Brevo envía el email de confirmación correcto;
5. el usuario pulsa el CTA de confirmación;
6. solo entonces pasa a estado confirmado/lista activa;
7. se produce la redirección/landing prevista;
8. una segunda alta con el mismo email no crea duplicados ni rompe el estado;
9. una baja posterior impide futuros envíos de marketing.

Probar también:

- email nuevo;
- email ya confirmado;
- email pendiente de confirmar;
- email previamente dado de baja;
- email inválido;
- honeypot;
- doble envío rápido;
- back/reload/BFCache;
- almacenamiento local bloqueado.

## `/gracias-suscripcion/`

Antes de cerrar la PR, revisar de nuevo la lógica de esta página. Históricamente existió riesgo de que una visita directa marcara `nl-subscribed=1` localmente aunque no hubiera confirmación real, suprimiendo el popup a un usuario no suscrito.

No asumir que sigue roto: reproducir primero en `main` actual. Si el bug existe, corregir en esta PR con regresión. Si ya está resuelto, documentar `VERIFIED_CLEAN`.

## Dominio y entregabilidad

Brevo documenta actualmente autenticación con:

- código Brevo;
- DKIM;
- DMARC.

Ruta actual orientativa: `Settings → Senders, Domains, IPs → Domains`.

El dominio de envío debe ser uno controlado por David. No utilizar `@gmail.com` como dominio autenticado.

### Regla DMARC

No reemplazar un registro DMARC existente sin leerlo antes. Brevo está desplegando un flujo nuevo de configuración de dominio y puede ofrecer autenticación automática, pero si ya existe DMARC conviene preservar una política válida y añadir solo lo necesario.

Brevo indica además que, para cumplir requisitos modernos de Gmail/Yahoo/Microsoft, el registro DMARC debe incluir `rua`; su ayuda propone `rua=mailto:rua@dmarc.brevo.com` cuando falta.

Claude debe registrar:

- dominio autenticado sí/no;
- DKIM validado sí/no;
- DMARC existente y política actual;
- `rua` presente sí/no;
- remitente visible;
- Reply-To;
- si existe subdominio de tracking/branded link;
- cualquier warning de entregabilidad.

No guardar valores DNS privados o credenciales si no hace falta; los registros públicos pueden documentarse si son útiles.

Fuentes oficiales:

- https://help.brevo.com/hc/es/articles/12163873383186-Autenticar-el-dominio-con-Brevo-c%C3%B3digo-Brevo-DKIM-DMARC
- https://help.brevo.com/hc/es/articles/35337929909778-Configurar-el-dominio-en-Brevo

## Remitente

Revisar qué opción inspira más confianza y coincide con la identidad pública. Preferencia conceptual:

- nombre visible: `David Porto Díaz` o `David Porto Díaz · Novedades`;
- dirección en dominio propio si existe y está operativa;
- Reply-To que David realmente lea.

No inventar una dirección en dominio propio si no existe todavía.

## Diseño de emails

Brevo dispone de editor Drag & Drop, vista móvil y preview/test. La implementación debe priorizar compatibilidad de email, no replicar literalmente el CSS de la web.

### Sistema visual recomendado

- una sola columna principal;
- ancho contenido aprox. 600–650 px;
- fondo claro y alto contraste;
- negro/gris muy oscuro + acento dorado/ocre de la web solo donde funcione bien en email;
- logo/firma de autor sobrios;
- botones grandes y legibles;
- máximo un CTA principal por bloque;
- imágenes optimizadas;
- `alt` útil en imágenes informativas;
- texto vivo, no convertir titulares/copy en imágenes;
- tipografías web-safe o fallback robusto;
- no depender de fuentes personalizadas para identidad.

Brevo recomienda revisar móvil y modo oscuro. Probar especialmente Gmail y Outlook, porque ambos pueden reinterpretar colores y estilos.

Fuentes:

- https://help.brevo.com/hc/es/articles/360016831820-Descripci%C3%B3n-general-del-editor-de-email-Drag-and-Drop
- https://help.brevo.com/hc/es/articles/360017383919-Optimizar-el-dise%C3%B1o-del-email-para-dispositivos-m%C3%B3viles-adaptado-a-dispositivos-m%C3%B3viles
- https://help.brevo.com/hc/es/articles/15417444091538-Crear-emails-compatibles-con-el-modo-oscuro

## Plantillas mínimas que sí merecen la pena

No crear 20 plantillas por anticipación. Dejar estas seis reutilizables:

1. **DOI / confirma tu suscripción**
   - asunto claro;
   - CTA único de confirmar;
   - texto breve;
   - identidad visual de la web;
   - no incluir promoción agresiva antes de confirmar.

2. **Bienvenida**
   - gracias;
   - qué recibirá;
   - enlaces a Manecillas, Samuel, Cuaderno y herramientas sin saturar;
   - CTA principal hacia la obra actual o muestra.

3. **Novedad / lanzamiento de libro**
   - portada;
   - 2–3 párrafos;
   - físico + Kindle cuando proceda;
   - CTA de compra correcto;
   - no inventar urgencia.

4. **Nuevo artículo/recurso**
   - resumen corto;
   - CTA al artículo;
   - uno o dos enlaces secundarios.

5. **Firma / evento**
   - fecha, hora, lugar;
   - mapa/enlace si procede;
   - CTA de evento.

6. **Fragmento / muestra**
   - contexto;
   - CTA de lectura/EPUB/Kindle según derechos y estado vigente.

## Automatizaciones

Solo automatizaciones con beneficio claro:

- DOI → bienvenida una vez confirmada;
- segmentación por interés/origen únicamente si se utilizará;
- opcional: aviso de lanzamiento/evento si cumple consentimiento y frecuencia.

No automatizar cadenas largas de nurturing porque la newsletter del autor es pequeña y la promesa pública es enviar solo cuando haya algo que valga la pena.

## Bajas y suppressions

Auditar:

- unsubscribe link en campañas;
- contacto dado de baja → no vuelve a marketing por un simple re-submit;
- hard bounce;
- complaint/spam;
- contactos bloqueados;
- rebotes transaccionales si aplica;
- limpieza de duplicados.

Brevo distingue contactos bloqueados por canal y permite revisar bajas, complaints y hard bounces.

Fuente:

- https://help.brevo.com/hc/es/articles/5311015528594-Ver-los-contactos-en-listas-bloqueadas-cancelaciones-quejas-hard-bounces

## Tracking y privacidad

Brevo permite anonimizar el tracking de aperturas/clics. Evaluar si conviene activarlo como política por defecto: mantiene métricas agregadas pero no vincula apertura/clic a una persona concreta.

Fuente:

- https://help.brevo.com/hc/es/articles/11643306229906--Puedo-hacer-que-el-seguimiento-de-aperturas-y-clics-de-mis-emails-sea-an%C3%B3nimo

### No usar `open rate` bruto como KPI principal

Brevo documenta que:

- Apple Mail Privacy Protection infla aperturas;
- desde 2025 el cálculo puede incluir actividad de bots;
- se puede filtrar MPP/bots para analizar participación humana.

Priorizar:

- clics humanos filtrados;
- visitas/conversión en la web;
- bajas;
- complaints;
- hard bounces;
- entregabilidad;
- crecimiento neto de suscriptores confirmados.

Fuente:

- https://help.brevo.com/hc/es/articles/4406537065618-Acerca-de-la-Protecci%C3%B3n-de-la-privacidad-de-Apple-Mail-MPP-y-la-actividad-de-los-bots-en-Brevo

## UTM / analítica

Definir un esquema simple y estable, por ejemplo:

- `utm_source=newsletter`
- `utm_medium=email`
- `utm_campaign=<slug-campaña>`
- `utm_content=<cta>` solo cuando ayude a distinguir CTAs.

No meter email, user id ni PII en URL/UTM.

## API / worker / secretos

La web no debe exponer API keys de Brevo en frontend ni repo.

Claude debe comprobar:

- qué key/credential usa el worker;
- que viva en secret/env del proveedor;
- que no exista una key antigua innecesaria;
- scope mínimo razonable;
- última actividad;
- que el worker gestione errores y reintentos sin duplicar contactos.

Si una key se va a rotar o borrar, hacerlo solo después de verificar qué integración la usa.

## Secuencia exacta para Claude

### Fase A · inventario

1. Entrar en Brevo.
2. Enumerar listas, segmentos y atributos.
3. Enumerar templates.
4. Enumerar automations.
5. Enumerar senders/domains.
6. Enumerar forms activos dentro de Brevo.
7. Comparar con la integración real de la web.

### Fase B · fuentes

1. Grep/sitewide de todos los `source` enviados por formularios.
2. Comparar con atributos/segmentos en Brevo.
3. Corregir nombres incoherentes en el owner real.
4. No crear listas redundantes.

### Fase C · entregabilidad

1. Revisar dominio.
2. DKIM.
3. DMARC.
4. remitente/Reply-To.
5. warnings.
6. test a Gmail + Outlook.

### Fase D · DOI

Ejecutar un alta real controlada desde cada superficie relevante y verificar logs/estado final.

### Fase E · diseño

Actualizar solo las plantillas realmente utilizadas y crear las seis reutilizables si faltan.

### Fase F · automatizaciones

Eliminar/desactivar duplicadas u obsoletas y dejar únicamente las útiles.

### Fase G · baja

Probar unsubscribe real y re-subscribe posterior sin saltarse el consentimiento.

### Fase H · QA

- Gmail web;
- Gmail Android/iOS si está disponible;
- Outlook web/desktop si está disponible;
- móvil 320/390;
- dark mode;
- imágenes bloqueadas;
- enlace roto;
- CTA físico/Kindle correcto;
- footer legal/baja;
- no hay checkbox visible de newsletter añadido por error.

## Evidencia a guardar

- estructura final de listas/segmentos sin PII;
- atributos y taxonomía `source`;
- nombres/IDs no sensibles de templates y automations;
- estado de dominio `authenticated`;
- DOI E2E;
- prueba de unsubscribe;
- capturas de diseño solo sin contactos/PII;
- bugs de repo corregidos y PR/CI correspondientes.

## Criterio de cierre

`DOMAIN_AUTHENTICATED · DOI_E2E_VERIFIED · SOURCES_MAPPED · CONTACT_MODEL_CLEAN · TEMPLATES_CURRENT · AUTOMATIONS_MINIMAL_AND_USEFUL · UNSUBSCRIBE_VERIFIED · SUPPRESSIONS_REVIEWED · METRICS_INTERPRETED_CORRECTLY · GMAIL_OUTLOOK_MOBILE_DARKMODE_QA_DONE · NO_VISIBLE_NEWSLETTER_CHECKBOX`
