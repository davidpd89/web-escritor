# Encargo: impedir credenciales embebidas en URLs de salidas públicas

Estado: **BORRADOR, SIN IMPLEMENTAR**. P2: prevención de publicación accidental.
Base: `c369f933e52073604adc2972f902191289992e08`.

## Evidencia reproducida

Prueba Node de funciones reales, sin red ni escritura, con URL íntegramente
sintética `https://demo-user:demo-pass@example.com/libro`:

- `validateInput('profile', {name:'Autora de prueba',url})`: valid=true;
  `buildJsonLd()` conserva usuario/contraseña en url.
- `validatePressKitModel()` con modelo mínimo válido y website=url: errors=[];
  `buildTextFiles().authorData.website` conserva ambos componentes.
- `validateMetaTags()` con libro/descripción/imagen/alt válidos: warnings=[];
  `buildMetaTags().canonical` conserva ambos componentes.

Archivos: `assets/jsonld-escritores-core.js` (`isHttpsUrl`),
`assets/kit-prensa-core.js` (`isHttpsUrl`), `assets/metadatos-libro.js` (`httpsUrl`).
En contraste, `assets/evento-escritor-core.js` ya rechaza username/password.

No se han encontrado credenciales reales, exfiltración ni vulnerabilidad remota.
El defecto consiste en tratar como enlace público válido una URL aportada por el
usuario que contiene userinfo, y copiarlo a metadatos/JSON destinados a compartir.
No afirmar que se probó la UI completa o un ZIP real: se verificaron los módulos.

## Encargo y aceptación

- Definir política común: URLs públicas HTTPS sin username/password, incluidos
  campos secundarios de imagen, autor, compra, perfiles y sameAs según consumidor.
- Rechazar con aviso claro, no eliminar credenciales silenciosamente y declarar
  válido un destino distinto. No mostrar contraseñas en mensajes de error/logs.
- Revisar generadores públicos equivalentes y compartir contrato/pruebas cuando
  sea útil, sin refactorización global innecesaria.
- Conservar URLs normales, parámetros y fragmentos legítimos, y escapes anti-XSS.
- [ ] Regresiones con userinfo sintético: usuario solo, contraseña y codificación.
- [ ] Entradas normales siguen aceptadas; los tres consumidores aplican política coherente.
- [ ] Ninguna salida ni mensaje contiene el componente sensible del caso rechazado.
- [ ] Recorrido browser de cada formulario; ZIP sintético y código generado inspeccionados.
- [ ] Tests de JSON-LD, metadatos y kit de prensa, versiones/hashes y CI en verde.
- [ ] Evidencia antes/después y verificación del SHA tras publicar.

Pruebas de partida: `tests/test-jsonld-escritores-core.mjs`,
`tests/test-metadatos-libro.mjs`, `tests/test-kit-prensa-core.mjs` y QA de publicación.
No usar secretos reales como fixtures ni ampliar este encargo a autenticación.

Otra IA continúa esta rama con implementación, tests y entrega. Esta PR contiene
solo el encargo y no debe fusionarse como si ya corrigiera los validadores.