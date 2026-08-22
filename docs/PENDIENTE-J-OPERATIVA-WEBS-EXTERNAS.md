# Pendiente J — Operativa asistida en webs externas

Fecha: 2026-08-23  
Rama base: `implementacion-web-2026`  
HEAD base auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR es un **recordatorio operativo ejecutable** para tareas que no se pueden cerrar mirando solo Git: Search Console, Brevo, Cloudflare y cualquier otro panel web que aparezca en las auditorías. No implementa cambios de producción por sí sola.

## 1. Objetivo

Cuando una auditoría marque algo como «externo», «requiere panel», «requiere login» o «no verificable desde Git», **no dejarlo indefinidamente como gate abstracto**.

La forma de resolverlo será:

1. abrir una instancia dedicada de Microsoft Edge con depuración remota;
2. conectar el agente local/Claude Code mediante CDP al puerto elegido;
3. navegar al panel requerido;
4. si la sesión no está autenticada, detenerse únicamente para que David haga login/2FA/captcha manualmente;
5. después del login, continuar la revisión/configuración desde el navegador controlado;
6. hacer cambios de uno en uno, esperar a que la UI confirme cada estado y guardar evidencia;
7. documentar exactamente qué se verificó/cambió y qué sigue pendiente.

La intención es reducir al mínimo el trabajo manual del usuario: **el usuario interviene solo cuando un proveedor exige autenticación humana o una decisión que no se deba inferir**.

## 2. Apertura de Edge controlable

En Windows, usar una instancia separada de Edge. Ejemplo con puerto `9222`:

```bat
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%TEMP%\david-web-ops-edge"
```

Si Edge está instalado en `C:\Program Files\Microsoft\Edge\Application\msedge.exe`, usar esa ruta. Si `9222` está ocupado, elegir otro puerto local libre, por ejemplo `9223`.

### Reglas

- utilizar un perfil dedicado mediante `--user-data-dir`; no engancharse al perfil habitual de Edge mientras esté abierto;
- exponer la depuración **solo en localhost**; no publicar el puerto en red ni abrirlo en el firewall;
- no guardar contraseñas, códigos 2FA, cookies o tokens en el repositorio;
- no copiar secretos desde DevTools a ficheros o PR;
- cerrar la instancia dedicada cuando termine la sesión operativa.

El agente local se conecta por Chrome DevTools Protocol a:

```text
http://127.0.0.1:9222
```

## 3. Login humano mínimo

Si una web muestra login, 2FA, captcha, passkey o consentimiento de cuenta:

1. el agente deja abierta exactamente la pantalla necesaria;
2. avisa: «Necesito que inicies sesión aquí»;
3. David completa credenciales/2FA/captcha manualmente;
4. David confirma que ya está dentro;
5. el agente retoma el control de la pestaña autenticada y hace el resto.

No intentar automatizar contraseñas, 2FA, captcha ni mecanismos antiabuso. Tampoco intentar simular comportamiento humano para eludir controles del proveedor.

## 4. Ritmo de ejecución

Las acciones en paneles externos deben ser pausadas y verificables:

- una acción significativa cada vez;
- esperar carga/confirmación antes de la siguiente;
- evitar clicks repetidos o envíos duplicados;
- volver a leer el estado después de guardar;
- si una acción es irreversible, económica, publica contenido, cambia DNS, activa producción o borra datos, detenerse y pedir confirmación explícita;
- capturar evidencia textual o screenshot cuando sea útil;
- no declarar «hecho» hasta volver a comprobar el estado final en el propio panel.

## 5. Google Search Console — checklist operativo

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

## 6. Brevo — checklist operativo

La parte de código vive en otras PR; esta operativa cubre lo que solo puede verificarse/configurarse en el panel real.

Comprobar:

- lista canónica usada por la web;
- atributos de contacto esperados (`SOURCE` y los que procedan);
- estado real de doble opt-in;
- plantilla/automatización que se dispara tras confirmar;
- URL de retorno tras confirmación;
- baja/unsubscribe;
- que una suscripción real desde cada origen relevante aterriza en la lista correcta;
- que no se promete por copy algo que la automatización real no entrega.

Si hay que crear/modificar una automatización:

- documentar antes el estado actual;
- hacer un único cambio lógico por vez;
- usar una dirección de prueba autorizada;
- confirmar recepción/confirmación/baja end-to-end;
- no modificar campañas históricas no relacionadas.

## 7. Cloudflare — checklist operativo

Cuando corresponda después de integrar el código correcto:

- revisar Worker correcto;
- verificar `BREVO_API_KEY` como secret sin exponer su valor;
- verificar `BREVO_LIST_ID`;
- revisar bindings/KV/D1/Rate Limiting/Turnstile solo si la PR aplicable los requiere;
- desplegar únicamente la versión de Worker compatible con el `script.js` que ya esté en producción;
- ejecutar smoke test real después del deploy;
- revisar logs únicamente para confirmar comportamiento, sin copiar PII a GitHub.

Cambios de DNS, dominios, rutas, producción o seguridad que puedan afectar al sitio requieren confirmación humana explícita justo antes de aplicarlos.

## 8. Otros paneles que aparezcan durante la auditoría

Esta misma operativa se aplicará a cualquier tarea futura que dependa de UI autenticada, por ejemplo:

- Google Search Console;
- Brevo;
- Cloudflare;
- Metricool;
- perfiles sociales o plataformas de publicación cuando exista una tarea concreta;
- paneles de editorial/retailer si se necesita verificar una URL comercial;
- cualquier servicio externo cuya configuración real no pueda demostrarse desde el repositorio.

No abrir un panel «por si acaso». Debe existir una tarea concreta y verificable.

## 9. Evidencia mínima al cerrar cada tarea externa

La persona/agente que la ejecute debe dejar constancia de:

- fecha;
- servicio y cuenta/propiedad usada, sin datos sensibles;
- estado inicial relevante;
- cambio realizado;
- estado final verificado;
- URL/ruta/pantalla donde se comprobó;
- si hubo login humano;
- si queda algún gate externo;
- si el resultado obliga a abrir una PR de código nueva.

Cuando sea razonable, añadir screenshot sin datos personales/secrets o una transcripción breve del estado del panel.

## 10. Qué NO debe hacerse

- no automatizar credenciales, 2FA o captcha;
- no intentar eludir sistemas anti-bot;
- no ejecutar acciones destructivas/reversibles sin confirmación;
- no enviar cientos de URLs a indexar en masa;
- no desplegar una versión incompatible del Worker;
- no activar automatizaciones de correo sin probarlas;
- no almacenar secretos/cookies/tokens en código, logs o PR;
- no confundir «pude abrir el panel» con «configuración verificada».

## 11. Orden sugerido cuando se retome

1. terminar/integrar primero las PR de código que afecten al servicio;
2. abrir Edge dedicado por CDP;
3. Search Console: propiedad + sitemap + URLs de lanzamiento;
4. Brevo: DOI/automatización/lista/orígenes;
5. Cloudflare: desplegar y verificar Worker compatible;
6. Metricool u otros paneles solo cuando exista una tarea concreta;
7. registrar resultados y abrir PR de código únicamente si la evidencia externa descubre un defecto real.

## 12. Criterio de cierre de esta PR

Esta PR no se cierra porque exista este documento. Se podrá cerrar cuando:

- las tareas externas actualmente conocidas hayan sido ejecutadas o explícitamente pospuestas por una dependencia real;
- Search Console haya sido revisado después del despliegue pertinente;
- Brevo/Cloudflare hayan sido verificados end-to-end cuando las PR de código correspondientes estén integradas;
- cualquier hallazgo nuevo tenga su PR/tarea específica;
- quede un registro de evidencia suficiente para no tener que repetir la investigación.

**No merge automático a `main`. No desplegar producción desde esta PR.**
