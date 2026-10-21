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
ISBN, título, autor y valoración. La prueba aislada actualiza una valoración.
La primera prueba de los 26 libros no produjo coincidencias; por tanto, esa
prueba no demuestra cobertura completa ni debe presentarse como tal.

Se mantienen independientes los proveedores y sus fechas reales. Un fallo no
renueva la fecha de un dato antiguo. Seis regresiones nuevas cubren identidades
erróneas, votos inválidos, enlaces extraños, conservación de datos y parada tras
denegación. Otra regresión verifica que una caída del proveedor detiene el lote
tras la primera consulta fallida. La batería suma **71 tests aprobados**.

Los resultados de las consultas se guardan en `.ci/providers/`, fuera de los
artefactos publicados. Las credenciales nunca se incluyen en código ni informes.
Las copias temporales locales de las dos claves se han eliminado después de
verificar los secretos de GitHub y las consultas reales.
La configuración de cuentas y los tests no equivalen a un despliegue de la PR.
