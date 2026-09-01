# J.5 · AMA asíncrono / preguntas al autor

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Matriz intermedia:** `IMPLEMENTAR/PILOTAR`  
**Trigger:** disponer de preguntas/audiencia reales y de tiempo editorial para responderlas con valor.  
**Forma preferida:** recopilación moderada + respuesta editada y publicada como contenido canónico; no comentarios públicos sin moderación.

## 1. Hipótesis original

J.5 proponía abrir periódicamente un espacio de preguntas y respuestas por escrito con el autor y publicar el resultado en el Cuaderno. El atractivo era doble:

- comunidad sin necesidad de una sesión en directo;
- contenido de primera mano, difícil de replicar y potencialmente útil para buscadores/asistentes porque responde cuestiones reales sobre obra, proceso y lectura.

#135 mantuvo el potencial, pero rechazó convertirlo en una feature permanente sin preguntas reales.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | AMA periódico escrito, publicado en Cuaderno. |
| Revisión 108/108 | `CONDITIONAL` | Puede producir contenido propio único; captar preguntas dentro/fuera, moderar y publicar respuesta editada. |
| Matriz operativa | `IMPLEMENTAR/PILOTAR` | Alto potencial editorial, especialmente con preguntas reales. |
| Repo cross-check/alternativas | preferido frente a foro | AMA/email/club permiten conversación sin crear identidad/comunidad persistente. |
| Autoridad final | `CONDITIONAL` | Solo con audiencia/preguntas reales; no abrir una superficie vacía. |
| Revalidación independiente | mantenido | J.1–J.6 mantienen estados; evitar identidad/moderación permanente sin demanda. |

La matriz elevó el atractivo, pero la autoridad final conserva el trigger. `CONDITIONAL` no significa “crear ahora una página AMA esperando que lleguen preguntas”.

## 3. Estado real de `main` al 29/08/2026

La web ya dispone de superficies que pueden originar preguntas sin un foro nuevo:

- `/clubes-de-lectura/samuel-entre-mundos/` incluye preguntas de debate y una vía para invitar al autor;
- newsletter/contacto pueden recoger interacción en contextos existentes;
- `/lectores-beta/` funciona como grupo pequeño/manual, no como comunidad pública;
- J.1 queda diferido precisamente para no abrir perfiles/hilos persistentes.

No se ha identificado en las autoridades inspeccionadas una superficie específica de AMA asíncrono que deba considerarse ya implementada.

Por tanto J.5 es una **posible pieza editorial**, no una reparación técnica.

## 4. Trigger correcto

Activar un piloto únicamente si se da una combinación como:

- un club, evento o lanzamiento produce varias preguntas genuinas;
- lectores/redes/email repiten cuestiones que merecen respuesta pública;
- existe un tema concreto con suficiente densidad para una pieza útil;
- el autor quiere dedicar tiempo a responder y revisar;
- existe una ventana editorial clara: publicación, aniversario, proceso creativo, sesión de club, etc.

No fijar una cadencia mensual/semanal artificial si no hay material.

## 5. Flujo preferido sin comunidad pública

### 1. Recogida

Las preguntas pueden llegar por:

- coordinador de un club;
- email/contacto;
- redes sociales;
- formulario temporal específico, si se justifica;
- evento presencial;
- lectores beta dentro de su finalidad correspondiente.

### 2. Moderación previa

Antes de publicar/responder:

- eliminar spam/abuso;
- quitar PII innecesaria;
- agrupar duplicadas;
- separar spoilers;
- rechazar preguntas que pidan datos privados/confidenciales;
- confirmar que se puede atribuir a una persona solo si existe permiso claro.

### 3. Respuesta humana

La respuesta debe ser del autor y mantener canon/factualidad. IA puede, como mucho, ayudar en un workflow privado a ordenar/transcribir/estructurar notas dentro de los límites de G.2/G.5; no debe fabricar la voz o experiencia personal del autor.

### 4. Edición

- corregir claridad/ortografía;
- preservar significado;
- marcar contexto/fecha;
- añadir enlaces canónicos útiles;
- introducir aviso de spoilers cuando corresponda;
- no convertir cada respuesta en promoción.

### 5. Publicación

Preferir una URL editorial canónica dentro de la familia adecuada (por ejemplo Cuaderno) antes que una aplicación de chat/comentarios.

## 6. Atribución y privacidad

Por defecto, la pregunta puede publicarse de forma anónima o agregada.

Si se quiere mostrar nombre/handle:

- pedir permiso explícito para esa atribución;
- no publicar email u otros datos de contacto;
- permitir retirar/corregir atribución cuando sea razonable;
- no inferir edad, ubicación u otros atributos.

Si un formulario nuevo recoge preguntas, I.2/I.5 deben registrar:

- campos;
- finalidad;
- retención;
- sistema receptor;
- spam protection;
- mecanismo de borrado.

No conservar un buzón histórico de preguntas sin finalidad.

## 7. Spoilers y canon

Clasificar la pieza o cada bloque cuando sea necesario:

- sin spoilers;
- spoilers de Samuel;
- spoilers de Manecillas;
- proceso creativo sin revelar trama;
- respuesta posterior a lectura completa.

La metadata/snippet no debe revelar un spoiler oculto en UI.

Para hechos verificables —fecha, editorial, ISBN, premios, disponibilidad— usar autoridades canónicas actuales, no memoria informal.

## 8. Moderación ≠ censura de preguntas incómodas

La moderación técnica/editorial existe para:

- seguridad;
- PII;
- repetición;
- relevancia;
- spoilers;
- límites de volumen.

No debe presentarse como un “AMA abierto” si solo se publicarán preguntas promocionales. El valor del formato depende de respuestas útiles y humanas.

## 9. No prometer respuesta individual

El copy de captación debe dejar claro, si aplica:

- se seleccionarán preguntas;
- no todas recibirán respuesta;
- las respuestas pueden agruparse/editarse;
- el envío no crea una relación privada de soporte;
- no enviar manuscritos/material confidencial por esa vía salvo que exista flujo específico.

Esto evita convertir un piloto editorial en un canal de atención ilimitado.

## 10. Estructura recomendada de la pieza publicada

Ejemplo:

```text
Título factual/editorial
Contexto y fecha
Aviso de spoilers

Pregunta 1
Respuesta
Enlaces relacionados

Pregunta 2
Respuesta
...

Cómo enviar futuras preguntas (solo si sigue abierto)
```

Puede incluir un índice si es largo, pero no necesita FAQ schema ni otra capa AEO artificial.

## 11. Medición útil

Para un piloto basta observar:

- número de preguntas válidas recibidas;
- cuántas son realmente distintas;
- temas repetidos que alimentan C.3;
- visitas/lecturas de la pieza con analítica ya existente;
- enlaces a obra/fragmento si son naturales;
- feedback cualitativo de clubs/lectores;
- coste editorial de responder/moderar.

No medir éxito por cantidad de preguntas si la mayoría es spam o repetición.

## 12. Relación con otras ideas

- **J.1:** AMA es alternativa preferida al foro persistente.
- **J.2:** preguntas de clubes por capítulos pueden convertirse en AMA posterior.
- **J.3:** si hay una ventana/encuentro fechado, el calendario existente puede reutilizarse; un AMA puramente asíncrono no necesita ICS.
- **J.6:** lectores beta pueden originar preguntas, respetando su consentimiento/finalidad.
- **C.3:** preguntas repetidas pueden convertirse en piezas independientes.
- **G.5:** no almacenar prompts/preguntas indefinidamente por analítica.
- **I.5:** cualquier formulario/retención debe minimizarse.

## 13. Qué no hacer

- No crear comentarios públicos o login para el AMA.
- No abrir un formulario permanente sin owner/moderación.
- No prometer respuesta a todo.
- No publicar PII del remitente.
- No fabricar preguntas para que la página parezca activa.
- No generar respuestas “en voz del autor” con IA.
- No publicar spoilers sin señalización.
- No crear FAQPage schema esperando rich results.
- No fijar una cadencia artificial sin audiencia/material.

## 14. Definition of Done para un piloto

- [ ] existe un conjunto real de preguntas/audiencia;
- [ ] tema/ventana editorial definidos;
- [ ] canal de entrada y moderación definidos;
- [ ] PII/retención documentados si hay formulario;
- [ ] atribución solo con permiso;
- [ ] respuestas humanas revisadas;
- [ ] canon/hechos comprobados;
- [ ] spoilers clasificados;
- [ ] pieza canónica publicada en familia adecuada;
- [ ] no se introduce login/foro/third-party comments;
- [ ] resultado y coste editorial evaluados antes de repetir.

## 15. Trazabilidad #135

Revisados:

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis J.5;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL`, preguntas moderadas y publicación editada;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR/PILOTAR`;
- repo cross-check/overrides — AMA como alternativa a foro/hilos;
- autoridad machine-readable;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — `CONDITIONAL`;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — estados J mantenidos.

## 16. Cierre

J.5 merece conservarse porque transforma preguntas reales en contenido original sin obligar al sitio a convertirse en una comunidad con cuentas y moderación permanente. Su calidad depende de que existan preguntas de verdad, respuestas humanas y una edición responsable; por eso el trigger sigue siendo parte de la decisión.