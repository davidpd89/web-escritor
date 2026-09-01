# D.6 · Revalidación de producción — quiz general de lectura

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **REJECT · GENERAL_QUIZ_NOT_JUSTIFIED · START_HERE_OWNS_ORIENTATION · PRESERVE_SAMUEL_SPECIFIC_QUIZ · NO_CODE**.

## 1. Resultado

No existe una necesidad actual que justifique un recomendador general «qué libro de David Porto leer». La orientación general ya tiene un owner más simple, visible y crawlable en `/empieza-aqui/`; el quiz existente de Samuel es una experiencia narrativa específica y no debe convertirse en plantilla para el catálogo.

## 2. `/empieza-aqui/` resuelve la tarea general

La página existe en `main`, es indexable y canónica. Su propuesta visible es:

> «¿Por dónde empiezas?»

> «No necesitas conocer la web. Elige lo que vienes a buscar y entra por ahí.»

Ofrece rutas explícitas hacia obra actual, fantasía, autor, lecturas, herramientas, prensa y otras necesidades reales. No requiere JavaScript para decidir ni oculta destinos detrás de preguntas.

Para el catálogo actual, esta arquitectura tiene menor coste y mayor claridad que un quiz general.

## 3. El quiz de Samuel es otra feature

`assets/samuel-quiz.js` está activo como experiencia específica del universo de `Samuel entre mundos`.

Tiene cinco preguntas narrativas y resultados como:

- El Mensajero;
- El Sabio del Espejo;
- La Silenciadora;
- El Guardián.

El código gestiona avance, foco, resultado, compartir y reiniciar. Su pregunta de producto es «qué perfil de Noveris eres», no «qué obra deberías leer».

Por tanto:

```text
quiz Samuel/Noveris existente
≠
recomendador general del catálogo
```

No se debe generalizar por reutilización técnica si la necesidad editorial es distinta.

## 4. Catálogo y discriminación

La investigación histórica ya concluyó que un catálogo pequeño produce decisiones triviales. La revalidación de producción no aporta evidencia nueva que cambie eso.

Un recomendador general solo tendría sentido cuando varias obras publicadas permitan discriminar de forma honesta por dimensiones editoriales reales: género, tono, estructura, compromiso, experiencia de lectura, etc.

No debe crearse para aumentar pasos, tiempo en página o sensación de interactividad.

## 5. Gate de reapertura

Reabrir solo si se cumplen conjuntamente:

```text
catálogo sustancialmente mayor
AND atributos comparables reales
AND lectores muestran dificultad repetida para elegir
AND /empieza-aqui/ deja de resolver bien el journey
AND resultados no triviales
AND QA/maintenance owner claro
```

Si se reabre, el resultado debe explicar por qué recomienda una obra y enlazar a una ficha/fragmento canónico.

## 6. Qué no hacer

- no convertir el quiz de Noveris en un recomendador genérico;
- no crear preguntas de personalidad que conduzcan artificialmente a uno de pocos libros;
- no usar un LLM para decidir una clasificación trivial;
- no almacenar perfiles del visitante;
- no duplicar `/empieza-aqui/`;
- no justificarlo por «engagement» o time-on-page;
- no añadir analytics/estado/runtime sin una tarea real que resolver.

## 7. Definition of Done

- [x] `/empieza-aqui/` verificado como owner actual de orientación;
- [x] quiz específico de Samuel inspeccionado directamente;
- [x] ambas funciones separadas;
- [x] ausencia de trigger nuevo confirmada;
- [x] rechazo histórico mantenido sin matar el quiz narrativo existente;
- [x] sin código nuevo.

## Estado para Claude

Mantener D.6 rechazada. Preservar el quiz específico de Samuel como experiencia propia; usar `/empieza-aqui/` para orientación general hasta que un catálogo futuro haga útil una recomendación genuinamente discriminante.