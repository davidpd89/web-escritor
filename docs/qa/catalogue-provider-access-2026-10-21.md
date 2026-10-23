# Acceso a proveedores del catálogo: comprobación del 21 de octubre de 2026

## Navegador

Se ha verificado el control de Edge mediante Playwright y Chrome DevTools Protocol.
El perfil de Amazon ocupaba el puerto local 9226. Un segundo perfil se había
iniciado con el mismo puerto: la conexión al 9226 llegaba a Amazon, sin mostrar
las pestañas de Google Cloud y Hardcover. Se ha reabierto exclusivamente el
perfil del catálogo con el puerto 9227, limitado a 127.0.0.1.

El perfil del catálogo conserva su directorio privado original. No es necesario
copiar cookies, desactivar protecciones ni cerrar los otros perfiles. Para
reconectar se usa `chromium.connectOverCDP('http://127.0.0.1:9227')`; siempre se
verifica el dominio y la pestaña antes de actuar. El usuario ha iniciado sesión.

## Google Books

- Proyecto creado, con autorización explícita: **David Porto - Libros**.
- Google asignó al enviar el formulario el ID **david-porto-libros**.
- Books API habilitada. Clave **David Porto - Books API** restringida a Books API;
  la lista de credenciales confirma esa restricción.
- Secreto del repositorio: `GOOGLE_BOOKS_API_KEY`, comprobado por nombre y fecha.
- No se ha añadido una cuenta de facturación ni contratado servicios de pago.
- Las consultas reales de Coraline devuelven HTTP 503 y el mensaje del proveedor
  `Service temporarily unavailable.` No se considera una conexión validada por
  haber creado una clave. El catálogo debe tolerar la indisponibilidad del proveedor.

Documentación: https://developers.google.com/books/docs/v1/using

## Hardcover

- Plan **Free**: la interfaz indica 60 consultas/minuto, ráfaga de 10 y 5000/día.
- Clave **David Porto - catalogo web**, creada tras autorización explícita.
- Único permiso: **read:catalog:data**. Sin escritura ni acceso a bibliotecas,
  correos, diarios o datos privados. Caducidad seleccionada: un año.
- Secreto del repositorio: `HARDCOVER_API_KEY`, comprobado por nombre y fecha.
- Consulta real, coincidencia exacta de ISBN, título y autor de Coraline:
  **4,03/5 con 1507 valoraciones**. Origen atribuido a Hardcover.
- Prueba de los 26 libros: 26 consultas, una valoración coincidente, 25 sin
  valoración coincidente y cero errores. No se inventan valores para completar
  fichas ni se atribuyen las valoraciones de Hardcover a Goodreads.

Documentación: https://docs.hardcover.app/api/getting-started/

## Goodreads y pruebas

La consulta pública por ISBN de Coraline devuelve su JSON-LD y permite comprobar
ISBN, título, autor y valoración. Tras corregir la reconciliación del proveedor,
el [piloto real de Actions 39584027168](https://github.com/davidpd89/web-escritor/actions/runs/39584027168)
consultó los 26 libros: **15 coincidencias de Goodreads**, 11 sin valoración y
cero errores; Hardcover obtuvo una coincidencia y Google Books respondió 503.
Los 16 registros de ambas fuentes corresponden a **15 libros distintos** y
forman parte de la entrega #665. La primera prueba sin coincidencias queda
superada por este piloto; ninguno de los dos demuestra cobertura completa.

Se mantienen independientes los proveedores y sus fechas reales. Un fallo no
renueva la fecha de un dato antiguo. Seis regresiones nuevas cubren identidades
erróneas, votos inválidos, enlaces extraños, conservación de datos y parada tras
denegación. Otra regresión verifica que una caída del proveedor detiene el lote
tras la primera consulta fallida. La batería de #665 sumó **101 tests aprobados**;
la recuperación de propuestas antiguas en #676 la amplía a **105**.

Los resultados de las consultas se guardan en `.ci/providers/`, fuera de los
artefactos publicados. Las credenciales nunca se incluyen en código ni informes.
Las copias temporales locales de las dos claves se han eliminado después de
verificar los secretos de GitHub y las consultas reales.
La clave de Hardcover tiene caducidad anual: requiere renovación antes de su
vencimiento, sin ampliar permisos. Si caduca o falla un proveedor, los demás
siguen disponibles y las valoraciones antiguas no se presentan como recién revisadas.

## Amazon y publicación

La aplicación y las credenciales de Creators API están creadas; la consulta real
del piloto devolvió `pending_amazon_eligibility`, sin ofertas. Amazon exige diez
ventas válidas en treinta días y advierte de hasta 48 horas de revisión inicial.
Esa advertencia no confirma que la cuenta ya tenga diez ventas ni garantiza
activar la API al terminar el plazo. No se copian precios manuales para fingir acceso.

La configuración de cuentas y los tests no equivalen por sí solos a un despliegue.
#665 pasó 32 controles reales y se publicó como `d31181d6287798f5d8447b7f371559a766d7cfe7`;
la verificación pública comprobó 106 archivos exactos y sus cinco resoluciones.
El ciclo diario y las mejoras posteriores conservan su evidencia en las PR y Actions.
