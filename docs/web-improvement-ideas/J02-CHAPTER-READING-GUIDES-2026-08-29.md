# J.2 · Guías de discusión por capítulo

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Matriz intermedia:** `PILOTAR`  
**Trigger:** un club real solicita o demuestra uso de una lectura por sesiones/capítulos. No producir una guía exhaustiva por anticipación.

## 1. Hipótesis original

J.2 proponía ampliar las guías de lectura desde el nivel de libro a un desglose capítulo a capítulo, pensado para clubes que se reúnen varias veces durante la lectura.

#135 concluyó que el formato puede tener mucho valor cuando existe un caso real, pero es contenido intensivo, sensible a spoilers y costoso de mantener. Por eso quedó `CONDITIONAL`.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Desglose descargable/usable capítulo a capítulo. |
| Revisión 108/108 | `CONDITIONAL` | Solo si clubes reales lo piden; coste editorial y spoilers. |
| Matriz operativa | `PILOTAR` | Puede ser contenido original de alto valor con una audiencia real. |
| Repo cross-check | infraestructura existente | Ya existe guía a nivel de libro; extender la autoridad actual, no crear otro ecosistema. |
| Autoridad final | `CONDITIONAL` | Trigger explícito de club/demanda real. |
| Revalidación independiente | mantenido | Evitar construir comunidad/contenido intensivo sin demanda. |

## 3. Estado real de `main` al 29/08/2026

`/clubes-de-lectura/samuel-entre-mundos/` ya es una autoridad sustancial:

- título y metadata específicos de guía de lectura;
- 10 preguntas de debate generales;
- ficha técnica/contexto;
- guía rápida para mediadores;
- temas de debate;
- CTA para invitar al autor;
- versión `/guia-imprimible/`;
- JSON-LD `Guide` + `LearningResource`;
- relación canónica con `Samuel entre mundos`.

Por tanto J.2 **no debe crear otra landing genérica de club**.

La pregunta correcta es: ¿un grupo concreto necesita avanzar por tramos/capítulos y la guía general ya no basta?

## 4. Por qué no producirla ahora por defecto

Una guía capítulo a capítulo:

- exige releer/verificar cada capítulo;
- introduce spoilers acumulativos;
- puede necesitar separar preguntas “antes/después de leer”;
- añade mantenimiento si cambia una edición;
- puede duplicar la guía general;
- puede convertirse en contenido de relleno si no hay uso real;
- exige decidir si el lector ve todo el índice de una vez;
- puede revelar estructura narrativa a lectores que aún no han llegado.

Su valor depende del contexto de uso, no de tener muchas URLs o PDFs.

## 5. Trigger exacto

Reabrir cuando exista al menos una señal fuerte:

- un club/coordinador pide explícitamente una guía por sesiones;
- se programa una lectura en varias reuniones;
- una biblioteca/instituto necesita material por bloques;
- se observa demanda repetida desde contacto/clubes;
- el autor va a participar en una secuencia de sesiones y necesita material estructurado.

No usar búsquedas genéricas de internet como única justificación.

## 6. Diseño editorial recomendado si se activa

### No necesariamente “un capítulo = una página”

Agrupar por unidades de lectura reales puede ser mejor:

```text
Bloque 1 · capítulos 1–4
Bloque 2 · capítulos 5–8
Bloque 3 · ...
```

La estructura debe seguir la dinámica del club y el libro, no una receta SEO.

### Por cada bloque

- rango de lectura;
- aviso de spoilers claro;
- 3–6 preguntas realmente distintas;
- uno o dos temas/decisiones narrativas;
- opcional actividad de mediación;
- notas para coordinador separadas de la experiencia del lector;
- enlace al siguiente bloque solo si no expone spoilers innecesarios.

## 7. Spoiler model

Antes de publicar definir niveles:

- `spoiler-free`: información segura antes de iniciar;
- `through-chapter-N`: puede revelar hasta ese punto;
- `full-book`: requiere haber terminado.

La navegación, títulos, snippets y metadata no deben revelar giros que el contenido intenta proteger.

No hacer que Google/social cards expongan una respuesta que la UI oculta detrás de “spoiler”.

## 8. Canonicalidad y formato imprimible

La guía actual ya tiene ruta web + imprimible.

Si J.2 se activa:

- preferir contenido canónico HTML útil;
- la versión de impresión debe derivarse del mismo contenido cuando sea posible;
- evitar duplicar texto indexable en múltiples URLs sin política clara;
- no generar un PDF pesado si print CSS resuelve el caso;
- mantener accesibilidad: headings, listas, contraste y orden lógico.

## 9. No convertirlo en scaled content

No crear automáticamente:

- 40 URLs para 40 capítulos;
- 10 preguntas generadas por IA por capítulo;
- resúmenes automáticos que sustituyen lectura;
- páginas vacías de “capítulo X preguntas” por búsqueda long-tail.

El valor competitivo es la guía de primera mano del autor/mediador, no el volumen.

G.2 puede ayudar con un borrador **privado** si se cumple su propio trigger, pero toda pregunta publicada debe tener revisión humana y canon correcto.

## 10. Señales de éxito

Con un club real, medir de forma sencilla:

- uso/descarga de la guía;
- feedback del coordinador;
- preguntas que realmente generan conversación;
- bloques que sobran/faltan;
- si repetiría el formato para otro grupo.

No hace falta analytics comportamental avanzado.

## 11. Relación con otras ideas

- **J.1:** no necesita hilos/comunidad pública.
- **J.3:** una lectura por sesiones puede reutilizar calendario ICS.
- **J.5:** preguntas buenas pueden alimentar un AMA posterior con permiso/contexto.
- **G.2:** IA solo como borrador editorial privado/revisado.
- **C.3:** preguntas repetidas de clubes pueden convertirse en contenido útil agregado.
- **C.4:** rights gate si se incluyen extractos sustanciales.

## 12. Qué no hacer

- No producir una guía completa sin club/demanda.
- No duplicar la landing de club ya existente.
- No crear una URL por capítulo por motivos SEO.
- No publicar spoilers en títulos/snippets inadvertidamente.
- No automatizar preguntas con IA y publicarlas sin revisión.
- No incluir citas largas si los derechos/editorial no lo permiten.
- No asumir que todas las ediciones tienen idéntica paginación.

## 13. Definition of Done si se activa

- [ ] existe un club/caso real documentado;
- [ ] rango de lectura por sesión definido;
- [ ] modelo de spoilers establecido;
- [ ] se reutiliza la guía canónica de Samuel/obra correspondiente;
- [ ] preguntas revisadas por el autor/humano;
- [ ] no hay scaled URLs;
- [ ] derechos de extractos revisados;
- [ ] versión imprimible deriva del contenido cuando proceda;
- [ ] accesibilidad verificada;
- [ ] feedback del club recogido de forma agregada;
- [ ] decisión posterior: mantener, ajustar o no repetir.

## 14. Trazabilidad #135

Revisados:

- banco original J.2;
- revisión: `CONDITIONAL`, solo bajo petición real y con coste/spoilers;
- matriz: `PILOTAR` con club real;
- repo cross-check: guía existente como autoridad;
- autoridad machine-readable;
- autoridad humana final: `CONDITIONAL`;
- revalidación independiente: estados J mantenidos.

## 15. Cierre

J.2 tiene potencial precisamente porque puede ser una pieza muy específica y útil para un club real. Si se fabrica antes de tener ese club, el mismo nivel de detalle se convierte en coste, spoilers y contenido sin uso. El trigger editorial es parte de la feature.