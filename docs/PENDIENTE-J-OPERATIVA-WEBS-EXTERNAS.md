# Pendiente J — Operativa asistida en webs externas SIN API/conector utilizable

Fecha: 2026-08-23  
Rama base: `implementacion-web-2026`  
HEAD base auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR es un **recordatorio operativo ejecutable exclusivamente para tareas externas que NO podamos resolver con una API, conector o herramienta ya disponible**. No debe usarse como sustituto de una API existente.

## 1. Regla principal: API primero, navegador solo si no hay vía programática utilizable

Antes de abrir Edge, comprobar siempre este orden:

1. ¿Existe conector/herramienta ya conectado en el entorno de trabajo?
2. ¿Existe API oficial y tenemos ya credenciales/API key válidas para usarla?
3. ¿Existe una CLI oficial/autorizada ya configurada?
4. Solo si las respuestas anteriores son negativas, o si la operación concreta **no está expuesta por la API disponible**, usar el procedimiento de navegador controlado descrito en esta PR.

Por tanto:

- **Brevo NO entra en esta operativa por defecto**: tenemos API key y las tareas que exponga la API deben hacerse por API.
- **Cloudflare NO entra en esta operativa por defecto**: tenemos credenciales/API y las tareas que exponga la API deben hacerse por API.
- **Metricool tampoco debe abrirse por navegador si el conector/API disponible permite la operación concreta.**
- Una UI web solo entra aquí cuando **no tenemos una vía programática utilizable para esa acción específica**.

Si una API cubre lectura pero no una operación concreta de configuración, solo esa operación residual puede pasar al navegador. Debe documentarse por qué no podía hacerse por API.

## 2. Objetivo

Cuando una auditoría marque algo como «externo», «requiere panel», «requiere login» o «no verificable desde Git», no dejarlo indefinidamente como gate abstracto.

Primero se intenta resolver mediante API/conector. Si no existe una vía programática utilizable, la forma de resolverlo será:

1. abrir una instancia dedicada de Microsoft Edge con depuración remota;
2. conectar el agente local/Claude Code mediante CDP al puerto elegido;
3. navegar al panel requerido;
4. si la sesión no está autenticada, detenerse únicamente para que David haga login/2FA/captcha manualmente;
5. después del login, continuar la revisión/configuración desde el navegador controlado;
6. hacer cambios de uno en uno, esperar a que la UI confirme cada estado y guardar evidencia;
7. documentar exactamente qué se verificó/cambió y qué sigue pendiente.

La intención es reducir al mínimo el trabajo manual del usuario: **el usuario interviene solo cuando un proveedor exige autenticación humana o una decisión que no se deba inferir**.

## 3. Apertura de Edge controlable

En Windows, usar una instancia separada de Edge. Ejemplo con puerto `9222`:

```bat
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%TEMP%\david-web-ops-edge"
```

Si Edge está instalado en `C:\Program Files\Microsoft\Edge\Application\msedge.exe`, usar esa ruta. Si `9222` está ocupado, elegir otro puerto local libre, por ejemplo `9223`.

### Reglas

- utilizar un perfil dedicado mediante `--user-data-dir`; no engancharse al perfil habitual de Edge mientras esté abierto;
- exponer la depuración solo en localhost; no publicar el puerto en red ni abrirlo en el firewall;
- no guardar contraseñas, códigos 2FA, cookies o tokens en el repositorio;
- no copiar secretos desde DevTools a ficheros o PR;
- cerrar la instancia dedicada cuando termine la sesión operativa.

El agente local se conecta por Chrome DevTools Protocol a:

```text
http://127.0.0.1:9222
```

## 4. Login humano mínimo

Si una web muestra login, 2FA, captcha, passkey o consentimiento de cuenta:

1. el agente deja abierta exactamente la pantalla necesaria;
2. avisa: «Necesito que inicies sesión aquí»;
3. David completa credenciales/2FA/captcha manualmente;
4. David confirma que ya está dentro;
5. el agente retoma el control de la pestaña autenticada y hace el resto.

No intentar automatizar contraseñas, 2FA, captcha ni mecanismos antiabuso. Tampoco intentar simular comportamiento humano para eludir controles del proveedor.

## 5. Ritmo de ejecución

Las acciones en paneles externos deben ser pausadas y verificables:

- una acción significativa cada vez;
- esperar carga/confirmación antes de la siguiente;
- evitar clics repetidos o envíos duplicados;
- volver a leer el estado después de guardar;
- si una acción es irreversible, económica, publica contenido, cambia DNS, activa producción o borra datos, detenerse y pedir confirmación explícita;
- capturar evidencia textual o screenshot cuando sea útil;
- no declarar «hecho» hasta volver a comprobar el estado final en el propio panel.

## 6. Google Search Console — ejemplo principal de esta operativa

Usar navegador **solo mientras no dispongamos en el flujo actual de credenciales/conector/API autorizada que permita realizar la operación concreta**.

Cuando se haga esta ronda, abrir Search Console con la propiedad de `davidportodiaz.com` y comprobar al menos:

### Propiedad y cobertura

- propiedad correcta seleccionada;
- método de verificación vigente;
- HTTPS/canonical coherentes;
- errores o avisos relevantes de indexación;
- páginas excluidas que no sean exclusiones deliberadas.

### Sitemaps

- comprobar si `https://davidportodiaz.com/sitemap.xml` está enviado;
- comprobar fecha/estado del último procesamiento;
- si no existe o está obsoleto y el sitio ya está desplegado correctamente, enviarlo/re-enviarlo;
- registrar cualquier URL del sitemap rechazada o no descubierta.

### Inspección de URLs clave

Tras el despliegue correspondiente, revisar como mínimo:

- `/`;
- `/las-manecillas-del-recuerdo/`;
- `/las-manecillas-del-recuerdo/fragmentos/`;
- `/libros/`;
- `/libros/samuel-entre-mundos/`;
- `/cuaderno/`;
- `/herramientas/`;
- otras URLs nuevas relevantes del lanzamiento.

Para cada una:

- comprobar canonical elegida por Google;
- comprobar indexabilidad;
- revisar último rastreo si existe;
- solicitar indexación solo cuando el HTML de producción sea ya el definitivo y no haya un gate conocido pendiente;
- no solicitar indexación para páginas deliberadamente `noindex`.

### Rendimiento

- registrar consultas/páginas con impresiones y CTR relevantes;
- no sacar conclusiones fuertes si el volumen es demasiado bajo;
- anotar anomalías reales que deban convertirse en una tarea posterior de SEO/contenido.

## 7. Qué servicios NO deben ir por Edge si ya tenemos API

### Brevo

Resolver por API todo lo que exponga la API usando la credencial existente: listas, contactos, atributos, plantillas, campañas/configuración disponible, verificaciones y pruebas automatizables.

Solo si una función concreta de Brevo **no está disponible mediante la API que podemos usar** —por ejemplo, una pantalla/automatización no expuesta— se podrá aplicar excepcionalmente esta operativa de navegador para esa función y se dejará escrito el motivo.

### Cloudflare

Resolver por API todo lo expuesto por las credenciales existentes: Workers, bindings, variables/configuración compatible, despliegues autorizados, zonas/rutas cuando proceda, etc.

No abrir el dashboard solo porque sea cómodo. El navegador queda reservado a una operación no disponible con nuestras credenciales/API o que requiera interacción humana del proveedor.

### Metricool y otros servicios conectados

Si existe conector/API capaz de ejecutar la tarea concreta, usarlo. Navegador únicamente como fallback para funciones no expuestas.

## 8. Otros paneles candidatos SIN API utilizable

Esta operativa puede aplicarse, cuando exista una tarea concreta, a servicios como:

- Google Search Console mientras no haya integración/API autorizada en nuestro flujo;
- perfiles o plataformas de publicación sin API útil para la acción requerida;
- paneles de editorial/retailer para verificar o configurar una URL comercial si no existe API;
- Amazon/KDP u otros backoffices cuando la acción no tenga una API autorizada disponible;
- servicios de premios, directorios, fichas de autor o plataformas similares sin API útil;
- cualquier servicio externo cuya configuración real no pueda demostrarse ni ejecutarse desde Git/API/conector.

No abrir un panel «por si acaso». Debe existir una tarea concreta y verificable.

## 9. Evidencia mínima al cerrar cada tarea externa

La persona/agente que la ejecute debe dejar constancia de:

- fecha;
- servicio y cuenta/propiedad usada, sin datos sensibles;
- por qué no pudo usarse API/conector para esa acción;
- estado inicial relevante;
- cambio realizado;
- estado final verificado;
- URL/ruta/pantalla donde se comprobó;
- si hubo login humano;
- si queda algún gate externo;
- si el resultado obliga a abrir una PR de código nueva.

Cuando sea razonable, añadir screenshot sin datos personales/secrets o una transcripción breve del estado del panel.

## 10. Qué NO debe hacerse

- no usar navegador si ya existe una API/conector utilizable para la misma acción;
- no automatizar credenciales, 2FA o captcha;
- no intentar eludir sistemas anti-bot;
- no ejecutar acciones destructivas/irreversibles sin confirmación;
- no enviar cientos de URLs a indexar en masa;
- no almacenar secretos/cookies/tokens en código, logs o PR;
- no confundir «pude abrir el panel» con «configuración verificada».

## 11. Orden sugerido cuando se retome

1. identificar el gate externo concreto;
2. comprobar primero API/conector/CLI disponibles;
3. resolver por API todo lo posible;
4. solo para el residuo no cubierto, abrir Edge dedicado por CDP;
5. pedir login humano si es necesario;
6. ejecutar la operación concreta y verificarla;
7. registrar evidencia y abrir PR de código únicamente si el resultado descubre un defecto real.

## 12. Criterio de cierre de esta PR

Esta PR no se cierra porque exista este documento. Se podrá cerrar cuando:

- los gates externos **sin API/conector utilizable** actualmente conocidos hayan sido ejecutados o explícitamente pospuestos por una dependencia real;
- Search Console haya sido revisado después del despliegue pertinente si sigue requiriendo UI;
- cualquier hallazgo nuevo tenga su PR/tarea específica;
- quede un registro de evidencia suficiente para no tener que repetir la investigación.

**Brevo y Cloudflare no son tareas de navegador por defecto: usar API.**  
**No merge automático a `main`. No desplegar producción desde esta PR.**
