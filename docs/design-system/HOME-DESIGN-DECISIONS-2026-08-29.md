# HOME — decisiones de diseño cerradas · 2026-08-29

Este fichero registra decisiones explícitas del autor que **no deben reinterpretarse como errores** durante la unificación visual de la HOME.

## 1. CTA de compra de «Las manecillas del recuerdo» antes del lanzamiento

Mientras «Las manecillas del recuerdo» no tenga todavía su destino comercial definitivo, el CTA «Comprar en Amazon» de la HOME **apunta de forma intencional al Amazon de «Samuel entre mundos»**.

El código de `assets/v1-home-editorial-v3.js` ya documenta este comportamiento mediante `MANECILLAS_BUY_URL = SAMUEL_AMAZON_URL`. No sustituirlo por una página informativa ni retirar el CTA sin una nueva instrucción explícita del autor.

## 2. Caja azul de contacto en «Eventos y encuentros»

La caja «¿Quieres organizar una presentación, firma o club de lectura?» **se mantiene como caja azul destacada**. No es un resto que deba convertirse en un bloque blanco/plano: funciona como recurso de énfasis, del mismo modo que la tarjeta azul «Lectores beta» en «Herramientas gratuitas».

Sí deben corregirse sus defectos de ejecución:

- el borde izquierdo de la caja debe quedar alineado con el rail y con el inicio de las rayas horizontales de los eventos;
- el borde derecho debe terminar en el mismo eje que esas rayas;
- el rail vertical debe conservar el grosor visual del sistema azul/dorado y no quedar tapado por el fondo de las tarjetas;
- el CTA «Escribir» debe respetar el contrato tipográfico de los enlaces de acción de la HOME, sin recuperar el subrayado convencional del sistema anterior.

## 3. Regla de trabajo

Durante esta migración se corrigen directamente errores objetivos de geometría, responsive, accesibilidad, estados de interacción, herencias CSS y restos inequívocos del sistema anterior.

Cuando una diferencia pueda ser una decisión visual deliberada —cambio de composición, tratamiento de una caja, eliminación de un énfasis, destino provisional de un CTA, etc.— debe consultarse antes de modificarla.
