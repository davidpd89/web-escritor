# QA manual de dispositivos y servicios reales

Owner: QA post-deploy.
Issue: #555.
Estado: pendiente de ejecucion manual con evidencia real.

Este documento existe para cerrar una frontera concreta: hay pruebas que los
checks headless de CI no pueden reproducir con fidelidad suficiente. No se deben
marcar como superadas por inferencia a partir de Playwright, Lighthouse, Pa11y o
smokes de produccion. Cada bloque requiere hardware, sistema operativo,
servicio externo o una cuenta real.

## Politica de cierre

Para cerrar el issue #555 tiene que existir una entrada de evidencia por cada
bloque de la matriz. Cada entrada debe incluir:

- fecha y zona horaria;
- persona que ejecuta la prueba;
- dispositivo fisico o servicio usado;
- sistema operativo y version;
- navegador, app o lector de pantalla y version;
- URL o flujo probado;
- resultado `PASS`, `FAIL` o `BLOCKED`;
- evidencia: captura, video, log exportado, ID de mensaje, ID de inspeccion o
  nota operativa reproducible;
- incidencias abiertas si el resultado no es `PASS`.

`BLOCKED` solo es valido si documenta el bloqueo externo y el siguiente paso.
No equivale a `PASS`.

## Matriz minima

### 1. Safari real en iPhone e iPad

Rutas minimas:

- `/`
- `/libros/`
- `/editoriales/`
- `/convocatorias-escritores/`
- `/metodologia-editorial/`
- un formulario con newsletter o lectores beta

Comprobar:

- navegacion normal desde carga fria;
- rotacion vertical-horizontal-vertical;
- zoom de texto del sistema;
- safe areas, notch y barras del sistema;
- teclado virtual en formularios;
- ausencia de scroll lateral y controles cortados.

PASS: la navegacion queda usable, el foco no se pierde y ningun control critico
queda fuera de viewport o tapado por el teclado.

### 2. PWA instalada en iOS

Instalar `https://davidportodiaz.com/` desde Safari en pantalla de inicio.

Comprobar:

- primer arranque tras instalacion;
- segundo arranque desde frio;
- actualizacion despues de un deploy nuevo;
- recuperacion despues de modo avion;
- comportamiento offline en rutas ya visitadas;
- salida limpia de modo offline a online.

PASS: la PWA arranca, actualiza version sin quedarse en cache antigua y muestra
fallback offline solo cuando corresponde.

### 3. Android Chrome con TalkBack

Rutas minimas:

- `/`
- `/libros/`
- `/editoriales/`
- `/convocatorias-escritores/`
- `/metodologia-editorial/`
- `/asistente/`
- formularios visibles de newsletter o lectores beta

Comprobar:

- navegacion por encabezados;
- landmarks;
- nombres accesibles de botones y enlaces;
- orden de foco;
- filtros de Editoriales y Convocatorias;
- anuncios de estado y errores;
- vuelta de foco al cerrar menus/dialogos.

PASS: no hay focos perdidos, controles sin nombre, filtros inoperables ni
contenido esencial inaccesible.

### 4. Windows con NVDA o JAWS

Navegador recomendado: Firefox o Edge actual.

Rutas minimas:

- Home;
- Obras;
- Editoriales;
- Convocatorias;
- Asistente;
- formularios de newsletter o lectores beta.

Comprobar:

- nombres accesibles;
- estados expandido/colapsado;
- anuncios live-region;
- errores de formulario;
- lectura de tarjetas;
- enlaces externos comprensibles sin contexto visual.

PASS: los flujos criticos se pueden completar sin raton y sin depender de
contenido puramente visual.

### 5. macOS con VoiceOver y Safari

Repetir la muestra critica de Windows/NVDA en Safari real.

Comprobar ademas:

- rotor de encabezados y landmarks;
- comportamiento de dialogos y menus;
- foco al volver desde enlaces externos;
- lectura de tarjetas y CTAs.

PASS: VoiceOver expone estructura, controles y estados de forma coherente.

### 6. Previews reales de enlaces externos

Servicios minimos:

- WhatsApp;
- Telegram;
- Discord;
- Slack;
- LinkedIn;
- X;
- Facebook.

URLs minimas:

- home;
- una pagina de libro;
- un articulo de Cuaderno;
- `/editoriales/`;
- una ficha editorial;
- `/convocatorias-escritores/`;
- `/metodologia-editorial/`.

Comprobar:

- titulo;
- descripcion;
- imagen;
- URL canonica;
- ausencia de asset roto;
- que no se herede por error la tarjeta generica de otra ruta.

PASS: cada servicio genera una tarjeta coherente con la URL compartida o se
documenta el cache externo y el depurador usado para refrescarlo.

### 7. Search Console y Bing Webmaster

Comprobar en ambas herramientas:

- cobertura/indexacion de `/editoriales/`;
- fichas editoriales representativas;
- `/convocatorias-escritores/`;
- `/metodologia-editorial/`;
- sitemap aceptado;
- canonica declarada frente a canonica seleccionada;
- renderizado/indexabilidad;
- ausencia de `noindex`, soft-404 o bloqueo de recursos inesperado.

PASS: no hay exclusiones nuevas no explicadas en las rutas criticas y los
sitemaps estan procesados sin errores operativos.

### 8. Brevo/newsletter end-to-end

Usar una cuenta de prueba controlada. Nunca usar direcciones de terceros.

Flujos minimos:

- alta desde home;
- consentimiento visible;
- email de confirmacion/double opt-in;
- confirmacion;
- baja;
- reintento/idempotencia;
- error de proveedor simulado o real controlado;
- flujo especifico de lectores beta si usa lista o atributo separado.

Registrar sin exponer PII:

- dominio del buzon de prueba, si procede;
- ID de mensaje o evento Brevo;
- lista/atributo afectado;
- estado final del contacto;
- captura o export sanitizado.

PASS: consentimiento, alta, confirmacion, baja, segmentacion y errores funcionan
sin duplicados ni filtracion de datos personales.

## Plantilla de evidencia

```md
## YYYY-MM-DD HH:MM Europe/Madrid - <bloque>

- Resultado: PASS | FAIL | BLOCKED
- Ejecuta:
- Dispositivo/servicio:
- SO/app/lector:
- Versiones:
- URLs/flujos:
- Evidencia:
- Incidencias:
- Notas:
```

## Fuera de alcance automatico

No convertir esta matriz en un gate automatico salvo que exista un entorno
fiable para esa comprobacion concreta. Los checks existentes de PWA, Pa11y,
Lighthouse, reflow, enlaces, Pagefind, consola, sitemap y produccion siguen
siendo necesarios, pero no sustituyen esta evidencia manual.
