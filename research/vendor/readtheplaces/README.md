# Read the Places · copia upstream sin adaptar (PR hija #666)

**Investigado/copiado el 21/10/2026.** [Proyecto](https://github.com/markselby9/readtheplaces.com). Esta carpeta es **solo referencia vendorizada**, no importada en el build, sin scripts, librerías, red, acciones ni deploy.

## Procedencia exacta y licencia

- [Original de places.ts](https://github.com/markselby9/readtheplaces.com/blob/main/packages/tools/src/places.ts) — blob Git `d4f8546d9b241d83e2b172646deeb37e03db70d2`; copia **literal** `packages/tools/src/places.ts`.
- [Original de normalise.ts](https://github.com/markselby9/readtheplaces.com/blob/main/packages/schema/src/normalise.ts) — blob Git `0f7c1a4ac4edffb0d49bafe750a2f8f1c931357e`; copia **literal** `packages/schema/src/normalise.ts`.
- [Original de freshness.ts](https://github.com/markselby9/readtheplaces.com/blob/main/packages/tools/src/freshness.ts) — blob `c5790af8842fc90d639e1ab88d35245b29da7530`; copia **literal** en `packages/tools/src/freshness.ts`. Compara SHA y conteo de libros del despliegue para detectar publicaciones desactualizadas. Futuro uso exige adaptar conteo a lugares/relaciones y origen real del commit.
- [Licencia original](https://github.com/markselby9/readtheplaces.com/blob/main/LICENSE) — blob `d660c595a57f6d86a80737db9089dee0ff3605fd`; conservada literal como `LICENSE.upstream`. El copyright del código es © 2026 Read the Places contributors; código de `packages/` **MIT** con obligación de conservar avisos.
- Licencia **distinta** de los datos del repositorio de origen: `books/*/{book,waypoints}.json` **CC BY-SA 4.0**. **No se han copiado** obras, pasajes, base editorial, fotos ni datos. Materiales terceros tienen derechos propios.

## ¿Qué nos aporta exactamente?

El fichero `findPlaces` detecta secuencias con sufijos ingleses Street, Avenue, Bridge, Park... y nombres de un gazetteer de prueba. Devuelve `name`, `mentions`, `firstPosition` y `proposedPassage`. Se usa para descubrir **candidatos** en textos legalmente procesables. Su código advierte un caso real: confunde «Bourton» de *Mrs Dalloway* con otro lugar real al geocodificar. **Una detección nunca publica un punto por sí sola.**

## Estado de reutilización

**Copiado tal cual, NO funcional por separado todavía:** `places.ts` importa `normalise` de `@rtp/schema`, alias del monorepo upstream que no existe aquí. Por decisión deliberada no se ha modificado la copia para evitar confundir reproducción exacta con adaptación. Además depende de Bun/TypeScript para ejecutarse y su `GAZETTEER` inicial es británico.

En PR posterior de ingeniería:
1. Decidir adaptador pequeño TS (o portar a Python; no necesario si se consume fuente estructurada).
2. Conectar `normalise` por import relativo o paquete propio, en **otra carpeta**; conservar la fuente original intacta.
3. Conservar licencia y copyright, apuntar a versión/commit y probar extracción con dominio público legalmente demostrado.
4. Añadir terminaciones de calles de distintos idiomas, evitar homónimos, descartar false positives y etiquetar `candidate`.
5. No almacenar/exponer `proposedPassage` si el texto está protegido; sustituir por referencia/capítulo y contexto propio.

**No vendorizamos todo el repositorio**: subir cientos de obras/imágenes ajenas y dependencias sin analizar consume mantenimiento, aumenta el bundle y mezcla licencias. Si vamos a usar librerías como Leaflet, la opción con menor coste futuro suele ser instalar versión fija de su paquete y conservar avisos; no copiar miles de líneas manualmente.

## Checklist

- [x] Archivo fuente copiado sin alterar.
- [x] Dependencia de normalización original copiada sin alterar.
- [x] Comprobador de frescura de despliegue MIT copiado sin alterar.
- [x] Licencia upstream completa copiada sin alterar.
- [x] SHA de cada blob y URL de origen registrados.
- [x] No importado ni ejecutado, cero impacto en web.
- [ ] Adaptación y pruebas de integración con datos reales (otra PR autorizada).
