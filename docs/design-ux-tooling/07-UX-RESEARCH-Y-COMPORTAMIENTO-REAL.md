# 07 — UX research y comportamiento real

## 1. Objetivo

No todas las decisiones visuales pueden resolverse mirando CSS, Figma o un score de accesibilidad.

Hay preguntas que requieren personas:

- ¿entienden qué es lo más importante?;
- ¿saben cuándo cambia una sección?;
- ¿encuentran una acción?;
- ¿interpretan correctamente una portada/ficha?;
- ¿saben dónde están dentro de una página larga?;
- ¿la navegación editorial se entiende sin explicación?;
- ¿el diseño transmite autor/libro/publicación y no SaaS/template?;

Esta capa evita que Claude se convierta simultáneamente en diseñador, usuario y juez.

## 2. Qué investigar primero

### P0 — comprensión

- Home: quién es David + obra principal + cómo explorar.
- Manecillas: de qué trata + muestra + disponibilidad.
- Samuel: de qué trata + fragmento + compra.
- Autor: identidad + obra + prensa/contacto.
- Cuaderno: qué es + qué leer.
- Herramientas: qué puedo hacer + dónde empezar.

### P1 — jerarquía móvil

Pregunta específica del proyecto:

> ¿Una persona distingue los grandes bloques de una página interior sin leerla entera?

### P1 — navegación

- Explorar;
- breadcrumbs;
- links relacionados;
- retorno Back;
- rutas desde Home a obra y contenido.

### P2 — preferencia

Solo después de comprobar comprensión/task success.

No priorizar «qué versión te parece más bonita».

## 3. Maze

Maze es la primera herramienta a evaluar para investigación no moderada porque permite trabajar con prototipos y sitios web reales.

### Casos de uso

- prototype testing;
- live website testing;
- mobile;
- comparación de variantes;
- tareas de navegación;
- preguntas abiertas/cerradas;
- medir success/completion según estudio.

### Regla

Usar 2–3 variantes cuando haya una decisión real. El producto soporta más, pero multiplicar opciones puede diluir la pregunta.

## 4. Diseñar tareas, no encuestas de gusto

### Mala pregunta

> ¿Te gusta más A o B?

### Mejor

> Imagina que alguien te recomienda «Las manecillas del recuerdo» y quieres saber de qué trata y leer una muestra. Empieza aquí.

Después medir:

- primer destino;
- recorrido;
- errores;
- tiempo aproximado;
- si completa;
- comentario final.

## 5. Tests de jerarquía

### 5-second / first-impression

Mostrar una pantalla brevemente y preguntar:

- ¿de qué página crees que se trata?;
- ¿qué era lo más importante?;
- ¿qué recuerdas?;
- ¿qué harías después?

Útil para:

- Home;
- book hero;
- Autor opening;
- Tools hub.

### Long-scroll segmentation

Permitir scroll breve y después preguntar:

> ¿Cuántas partes principales recuerdas y cuáles eran?

Comparar baseline vs propuesta.

Esto ataca directamente el problema «todo va seguido».

### Findability

> Encuentra dónde contactar para una entrevista.

> Encuentra una herramienta para revisar repeticiones.

> Encuentra información sobre la magia de Noveris.

## 6. Tests por familia

## 6.1. Libro

Tareas:

- identificar género/tono;
- encontrar fragmento;
- comprobar disponibilidad;
- reconocer editorial/fecha si interesa;
- ir a contenido relacionado.

Preguntas:

- ¿qué elemento dominó demasiado?;
- ¿la portada ayudó o bloqueó?;
- ¿la ficha técnica se entendió como secundaria?

## 6.2. Autor

- saber quién es;
- localizar libros;
- identificar trayectoria;
- localizar prensa/contacto.

## 6.3. Artículo

- reconocer título/tema;
- orientarse mediante TOC;
- encontrar una sección concreta;
- identificar fuentes;
- encontrar relacionado.

## 6.4. Herramienta

- comprender qué hace antes de interactuar;
- realizar tarea;
- interpretar resultado;
- saber siguiente paso.

## 6.5. Prensa/Eventos

- encontrar próxima/última actividad;
- obtener press kit;
- localizar contacto;
- distinguir próximo vs histórico.

## 7. Participantes

No existe un número mágico universal.

Para investigación cualitativa temprana puede ser suficiente una muestra pequeña y diversa que permita descubrir problemas repetidos. No presentar esos resultados como estadística poblacional.

Segmentos útiles según tarea:

- lectores habituales;
- personas que no conocen a David;
- escritores que usarían herramientas;
- lector juvenil/adulto cuando proceda;
- prensa/organizador para tareas profesionales.

No mezclar todos los perfiles en cada estudio si la tarea es específica.

## 8. Moderado vs no moderado

### No moderado

Bueno para:

- navegación clara;
- variante A/B;
- tareas breves;
- first impression;
- comparación repetible.

### Moderado

Mejor cuando queremos entender:

- por qué no se percibe jerarquía;
- qué esperan de una página de autor;
- cómo interpretan elementos editoriales nuevos;
- qué les confunde de una composición no convencional.

No hace falta una plataforma específica para hacer cinco entrevistas moderadas por videollamada si esa es la necesidad.

## 9. Mobile real

No asumir que un test de prototipo dentro de un iframe desktop representa mobile.

Cuando el estudio sea sobre mobile:

- usar dispositivo real si es posible;
- controlar si el producto de research abre browser externo/app;
- documentar browser bars;
- no sacar conclusiones de gestos que el prototipo no puede reproducir.

## 10. Baseline primero

Antes de probar una solución, medir la versión actual.

Sin baseline, un resultado «7 de 10 lo encontró» dice poco.

Guardar:

- estudio;
- fecha;
- URL/commit;
- participantes/segmento;
- tareas;
- resultados;
- observaciones;
- decisiones.

## 11. No convertir métricas UX en ranking único

No crear un `UX Score 93` sin significado.

Separar:

- task success;
- misclicks;
- rutas;
- comprensión;
- recuerdo;
- confianza;
- comentarios cualitativos;
- problemas severos.

## 12. Clarity — gate condicional

Microsoft Clarity puede aportar comportamiento real mediante heatmaps/recordings, pero no está activado en el modelo actual de privacidad del sitio.

### Antes de instalar

- definir pregunta de investigación;
- revisar audiencia;
- revisar requisitos de consentimiento vigentes en EEA;
- decidir qué datos se recogen;
- revisar masking;
- actualizar privacidad;
- limitar duración del experimento;
- establecer owner y fecha de retirada.

### Casos donde podría aportar

- comprobar profundidad de scroll en páginas interiores;
- ver si una sección importante se ignora;
- detectar clicks en elementos no interactivos;
- observar dificultad con navegación.

### Casos donde no aporta

- decidir estética;
- sustituir entrevistas;
- inferir intención de un heatmap sin contexto;
- recopilar datos indefinidamente «por si acaso».

## 13. Alternativa low-tech

Antes de añadir session recording:

1. enviar preview a 5–8 personas apropiadas;
2. dar una tarea;
3. pedir grabación de pantalla opcional/consentida;
4. hacer 3 preguntas;
5. codificar problemas.

Puede dar más valor que meses de heatmaps sin pregunta.

## 14. Research repository

Proponer en repo, fuera del public artifact:

```text
docs/design-research/
  studies/
    2026-xx-mobile-hierarchy-article.md
  findings/
  decisions/
```

No guardar información personal de participantes innecesaria.

## 15. Severidad de hallazgos

### S0 — bloqueo

No puede completar tarea / contenido inaccesible.

### S1 — grave

Completa con errores importantes o interpreta mal la página.

### S2 — fricción

Lo consigue pero duda, retrocede o necesita demasiado scroll.

### S3 — refinamiento

Preferencia, microcopy, detalle visual.

Priorizar S0/S1 antes de cambios cosméticos.

## 16. Cómo usa Claude los resultados

Claude recibe findings, no raw recordings interminables.

Formato:

```yaml
finding: R-07
family: article-mobile
severity: S1
observed: 6/8 participantes interpretaron TOC como el inicio del artículo y no identificaron cuándo empezaba el texto
hypothesis: TOC ocupa demasiado peso y no existe transición suficiente hacia prose
next: explorar 2 composiciones compactas; preservar accesibilidad y anchors
```

Las cifras solo se usan si el estudio realmente las produjo.

## 17. No usar IA como participante ficticio

Claude puede hacer heuristic review, pero no se registra como «usuario».

No simular 20 personas con LLMs y presentar el resultado como user research.

IA puede:

- preparar guion;
- analizar notas;
- agrupar feedback;
- detectar temas;
- redactar hipótesis.

La evidencia humana debe seguir identificada como humana.

## 18. Sesgo

Evitar:

- explicar la intención antes del test;
- decir «hemos mejorado la jerarquía»;
- enseñar solo variante nueva;
- reclutar únicamente personas que conocen el proyecto;
- preguntar «¿te resulta fácil?» en vez de observar tarea;
- interpretar silencio como éxito.

## 19. Gate para cambios de alto impacto

Solicitar evidencia humana cuando un cambio:

- reorganiza navegación;
- cambia orden narrativo mobile;
- introduce un patrón nuevo;
- oculta/colapsa información antes visible;
- cambia una tarea principal;
- pretende explícitamente mejorar comprensión/findability.

No exigir research formal para corregir 8 px de overflow.

## 20. Criterio final

El research sirve para que el diseño deje de responder a:

> «Claude cree que esto se ve mejor»

Y pase a responder a:

> «Este cambio resuelve un problema observado, y sabemos qué evidencia demostraría que lo ha resuelto.»