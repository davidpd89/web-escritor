# D.6 · Quiz general de recomendación de lectura

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## 1. Hipótesis original

Extender el patrón de quiz de Noveris a un quiz general «qué deberías leer de David Porto», apoyándose en la idea de que contenido interactivo puede aumentar tiempo en página.

La hipótesis inicial partía de una señal secundaria genérica de engagement, no de una fricción demostrada en el sitio.

## 2. Evolución de la decisión

### Revisión → `REJECT`

#135 concluye que con dos libros principales no existe suficiente discriminación para justificar un recomendador general. La alternativa es mejorar `/empieza-aqui/` y conservar el quiz específico que sí tiene contexto.

### Matriz intermedia → `PILOTAR`

La matriz ensaya una condición más favorable:

> quiz solo si produce una recomendación genuina y conduce a fragmento/libro, no como engagement vacío.

Este `PILOTAR` no demuestra que el catálogo actual permita una recomendación genuina; define el estándar que tendría que superar.

### Autoridad final → `REJECT`

El cierre vuelve al rechazo:

> «Quiz general con dos libros no relacionados aporta poca discriminación y mucha superficie de mantenimiento. Reabrir con catálogo mayor.»

### Revalidación independiente

D.1–D.12 se mantienen. La conclusión no cambia.

## 3. Por qué el catálogo actual no justifica el quiz

Un buen recomendador necesita diferencias suficientemente ricas para que las respuestas del usuario cambien el resultado de forma no trivial.

Con un catálogo pequeño, el flujo tiende a convertirse en:

```text
pregunta obvia
→ clasificación obvia
→ uno de dos destinos
```

Eso añade:

- JS;
- estados;
- accesibilidad;
- copy;
- analytics;
- mantenimiento editorial

sin aportar más que una landing de orientación bien escrita.

## 4. No confundir con el quiz real de Samuel

`script.js` documenta que el antiguo `quiz-noveris-app` fue eliminado y que el quiz real vigente usa `samuel-quiz-app` + `assets/samuel-quiz.js` en la ficha de Samuel.

Ese quiz tiene un contexto narrativo/específico. Su existencia **no valida** D.6.

D.6 habla de un recomendador general del catálogo.

## 5. Alternativa principal: C.8 `/empieza-aqui/`

C.8 ya resuelve orientación mediante rutas explícitas sin esconder la decisión detrás de una mecánica de quiz.

Ventajas:

- crawlable;
- funciona sin JS;
- menos pasos;
- menor mantenimiento;
- copy directamente revisable;
- permite múltiples intenciones además de «qué libro leer».

Mientras el catálogo sea pequeño, esta solución es superior.

## 6. Qué sería una recomendación genuina

Si el catálogo crece, un futuro quiz debería usar dimensiones editoriales reales, por ejemplo:

- género/subgénero;
- tono;
- estructura;
- longitud/compromiso;
- fantasía vs narrativa especulativa/familiar;
- tipo de experiencia de lectura;
- tolerancia a ciertos elementos temáticos.

No usar personalidad inventada tipo «eres un soñador» si no cambia una recomendación útil.

## 7. Trigger de reapertura

El estado `REJECT` puede revisarse cuando exista:

```text
catálogo suficientemente amplio
AND atributos editoriales comparables
AND decisiones no triviales
AND destino útil por resultado
AND mantenimiento sostenible
```

Idealmente además:

- preguntas reales de lectores muestran dificultad para elegir;
- C.8 ya no resuelve bien la tarea;
- se puede probar el journey con teclado/lector de pantalla.

## 8. Arquitectura si algún día se reabre

Los resultados deben derivar de una autoridad de obras/metadata, no de reglas hardcoded dispersas.

Modelo conceptual:

```text
answer dimensions
→ scoring transparente y determinista
→ obra(s) compatibles
→ explicación de por qué
→ fragmento/ficha canónica
```

No usar un LLM remoto para decidir entre dos libros.

## 9. Accesibilidad

Un quiz futuro exige:

- fieldsets/legend cuando proceda;
- navegación completa por teclado;
- foco después de avanzar/mostrar resultado;
- estado y errores perceptibles;
- no depender solo de tarjetas clicables;
- back/restart claros;
- reduced motion.

Ese coste forma parte del rechazo actual.

## 10. Métricas

Si se reabre, medir:

- completion rate;
- abandonos por paso;
- clicks a fragmento/ficha;
- si el resultado distribuye de verdad entre obras;
- feedback cualitativo.

No justificar el quiz por «time on page» solamente: más pasos pueden inflarlo sin mejorar la tarea.

## 11. Qué NO hacer

- quiz general con dos resultados obvios;
- preguntas de personalidad sin base editorial;
- «engagement» como único objetivo;
- crear perfiles psicológicos del visitante;
- almacenar respuestas innecesariamente;
- usar IA para inventar recomendaciones;
- duplicar `/empieza-aqui/`;
- convertir el quiz específico de Samuel en plantilla global.

## 12. Relación con otras ideas

- C.8: alternativa principal actual.
- G.1: recomendación conversacional también debe basarse en catálogo real; no justifica D.6.
- D.11: si un quiz existiera, sus estados vacíos/error tendrían que cubrirse.
- D.1: microfeedback puede mejorar controles, pero no justifica el producto.

## 13. Pasadas posteriores revisadas

Cuarta–decimoquinta: no aparece evidencia que cambie D.6. La revalidación final mantiene los rechazos de interacción sin valor neto suficiente. Ninguna tendencia de quizzes se eleva por encima del estado real del catálogo.

## 14. Trazabilidad

- lista inicial — quiz general;
- revisión — `REJECT`;
- matriz — `PILOTAR` solo con recomendación genuina;
- autoridad final — `REJECT` hasta catálogo mayor;
- revalidación independiente — mantenida;
- `script.js` actual — separación respecto al quiz específico de Samuel.

## 15. Definition of Done de esta reconstrucción

- [x] contradicción `REJECT → PILOTAR → REJECT` preservada;
- [x] quiz específico vs general separados;
- [x] alternativa `/empieza-aqui/` documentada;
- [x] trigger de catálogo mayor definido;
- [x] no se crea runtime.

## Recomendación para Clara/Claude

No implementar D.6 ahora. Reabrir únicamente si el catálogo crece lo suficiente como para que un recomendador produzca decisiones útiles y no triviales.