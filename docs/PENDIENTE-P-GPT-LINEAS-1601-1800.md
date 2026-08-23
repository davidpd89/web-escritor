# Pendiente P — Auditoría GPT líneas 1601–1800

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `pendiente funcionalidad gpt.txt`, exactamente líneas 1601–1800.

## Regla de alcance

Este documento registra únicamente deuda que sigue siendo real después de contrastar el TXT con el código, datos, tests, CI y PR abiertas. No convierte en tarea una descripción antigua, una funcionalidad ya implementada, una publicación deliberadamente gated ni trabajo ya asignado a otra PR.

No tocar `main`, no desplegar producción y no activar auto-merge desde esta rama.

---

## 1. Continuación del documento 58 — Distribución de POV

**Clasificación: YA DETECTADO — #72 O.2.**

Las líneas 1601–1623 continúan exactamente el problema ya abierto en la PR #72. No justifican una PR nueva.

El cierre de O.2 debe incluir:

- detección robusta del formato de entrada;
- soporte explícito de `POV | palabras` como segundo contrato real;
- preservación de `escena | POV | palabras opcionales`;
- no reinterpretar silenciosamente dos columnas con semántica distinta;
- warnings claros para orden/tipo de columnas ambiguo o incoherente;
- orden de salida explícito y determinista;
- tests para ambos formatos y sus casos ambiguos.

No ampliar el alcance a inferir POV desde la prosa ni a construir un sistema estadístico general.

Se ha dejado comentario de coordinación en #72.

---

## 2. Documento 59 — «¿Qué tipo de lector eres?»

**Clasificación: DEUDA NUEVA — P.1.**

El TXT define una herramienta pública/local en `/herramientas/que-tipo-de-lector-eres/` y la considera un hueco de producto real.

### Estado verificado

En `implementacion-web-2026`:

- no existe la ruta `/herramientas/que-tipo-de-lector-eres/`;
- no existe un motor o fichero registrado para este quiz;
- `data/tools-hub.json` no contiene esta herramienta;
- las búsquedas de código no encuentran implementación equivalente;
- ninguna PR abierta #54–#72 cubre este producto.

### Contrato mínimo de implementación

Construir una herramienta que funcione completamente en navegador y sin cuenta.

Perfiles previstos por el documento, manteniendo un conjunto compacto de 5–7 resultados mutuamente distinguibles:

- detector de pistas;
- explorador de mundos;
- lector de personajes;
- lector de ritmo;
- lector emocional;
- lector de estilo.

El nombre final y la microcopy pueden ajustarse, pero no debe convertirse en un test psicológico, diagnóstico ni segmentación remota.

### Requisitos técnicos

- procesamiento local;
- sin enviar respuestas individuales a servidor/analytics;
- resultado reproducible para las mismas respuestas;
- preguntas y puntuación separadas de la capa de presentación;
- tie-break determinista y documentado;
- controles accesibles por teclado y lector de pantalla;
- resultado comprensible sin depender solo de color;
- integración en `data/tools-hub.json` y generación vigente del hub;
- CSP/privacidad coherentes con el contrato de herramientas locales;
- test unitario del scoring + smoke de UI;
- si se mide uso, solo evento agregado de apertura/completado conforme a la taxonomía de #63, nunca respuestas ni perfil obtenido.

### No hacer

- no almacenar un perfil de usuario;
- no pedir email para ver el resultado;
- no crear recomendaciones comerciales disfrazadas del resultado;
- no afirmar rasgos personales fuera de la preferencia de lectura que mide el propio cuestionario.

---

## 3. Documento 60 — «Esta web, en cifras»

**Clasificación: HECHO / GATED.**

La infraestructura existe:

- `scripts/build-human-site-stats.py`;
- `data/site-human-stats.generated.html`;
- `data/site-human-stats.generated.json`;
- gate de reproducibilidad en CI ya existente.

La decisión de no crear aún `/estadisticas/` con solo tres métricas humanas útiles es coherente con el propio TXT. Crear la página ahora sería inflar una superficie sin masa suficiente.

No abrir deuda nueva.

---

## 4. Documento 61 — Listas de lectura curadas

**Clasificación: PARCIAL / GATED / YA CUBIERTO POR #66 K.1.**

La infraestructura existe actualmente:

- `data/reading-list.json`;
- `data/reading-list-template.json`;
- `scripts/build-reading-list.py`.

El bloqueo real es editorial/evidencial: listas pequeñas, criterio explícito, fuente/evidencia y no atribuir lecturas personales no demostradas. Esa política pertenece al contrato de recomendaciones verificables de #66 K.1.

No abrir una segunda PR para lo mismo ni publicar `/listas-de-lectura/` por cumplir una ruta vacía.

---

## 5. Documento 62 — Web Lab

**Clasificación: HECHO / GATED.**

El TXT usa un nombre de fichero que ya no coincide con HEAD, pero la infraestructura sí existe.

Fuente vigente:

- `data/web-lab-entries.json`;
- `scripts/build-web-lab-index.py`;
- `scripts/validate-web-lab-entry.py`.

`data/web-lab-entries.json` contiene dos candidatos y ambos siguen `publish:false`.

El builder solo permite generar el hub público cuando hay al menos dos piezas publicables válidas. Eso coincide con el gate descrito: no publicar un laboratorio vacío ni convertir observaciones de un único sitio en leyes generales.

No abrir deuda nueva.

---

## 6. Documento 63 — Export de resultados / transparencia de método y licencia

**Clasificación: PARCIAL + DEUDA NUEVA — P.2.**

Existe una infraestructura de export open-source:

- `data/open-source-tools.json`;
- `scripts/build-open-source-export.py`.

La licencia raíz está deliberadamente en `null`. El builder lo trata correctamente como bloqueo y genera `LICENSE-REQUIRED.txt`; **elegir MIT o Apache-2.0 es una decisión humana y no forma parte de esta PR**.

### Gap técnico verificable

La entrada de Legibilidad declara:

- `files: ["legibilidad-engine.js"]`;
- `third_party: []`.

Pero el grafo real es:

`legibilidad-espanol.js` → `legibilidad-engine.js` → `silabajs-lite-2.1.0.js`.

`silabajs-lite-2.1.0.js` declara expresamente que es una adaptación de `silabajs 2.1.0`, upstream Nicolás Cofré Méndez, licencia MIT.

El exportador actual valida que cada fichero **declarado** exista, pero no analiza/importa el cierre transitivo del módulo. Tampoco verifica que una dependencia third-party real esté reflejada en `third_party` y en `THIRD_PARTY_NOTICES.md`.

Por tanto, activar `export:true` para Legibilidad en el estado actual puede producir un paquete incompleto: `legibilidad-engine.js` importaría un módulo que no viaja en el export. Además, el aviso «Sin dependencias de terceros declaradas» sería falso por omisión.

### Contrato de cierre P.2

Antes de habilitar cualquier `export:true`:

1. El manifiesto debe declarar el conjunto de ficheros necesario para ejecutar cada herramienta exportada.
2. El validador debe detectar imports locales estáticos y fallar si un import requerido queda fuera del paquete, o existir una alternativa equivalente que garantice closure de forma determinista.
3. Dependencias de terceros/adaptaciones deben quedar declaradas con nombre, origen y licencia.
4. `THIRD_PARTY_NOTICES.md` debe generarse a partir de esa autoridad, no de una lista opcional que puede quedar vacía incorrectamente.
5. Debe existir test de fixture que demuestre que un import transitivo omitido falla.
6. Debe existir test específico de Legibilidad que compruebe que el staging exportado puede resolver su grafo de módulos.
7. `--check` debe validar no solo hashes ya listados, sino también que el manifest actual y el staging siguen correspondiéndose con el contrato de fuentes.
8. Mantener `license: null` y `export:false` mientras no exista decisión humana de licencia/publicación.

### Fuera de alcance

- no crear un repositorio externo;
- no publicar código automáticamente;
- no elegir licencia por el propietario;
- no cambiar la licencia upstream de `silabajs`;
- no asumir que toda la web queda bajo la licencia futura del paquete de herramientas.

---

## Resultado del bloque 1601–1800

Deuda nueva real:

- **P.1** — construir «¿Qué tipo de lector eres?» como herramienta local, accesible y testeada;
- **P.2** — cerrar el grafo de dependencias y los avisos/licencias de terceros del export antes de habilitarlo.

Reutilizado, sin duplicar:

- POV → #72 O.2;
- evidencia de recomendaciones/listas → #66 K.1.

Gated correctamente:

- página dedicada de estadísticas;
- publicación de listas de lectura hasta tener evidencia;
- Web Lab hasta que existan dos casos publicables;
- elección/publicación de licencia open-source.

**STOP exacto: línea 1800.** No se interpreta la continuación del documento 63 desde la línea 1801 en esta ronda.
