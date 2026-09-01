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

## 3. «Obras» y «Para escribir» siguen siendo bloques

Las secciones «Libros y territorios» y «Herramientas gratuitas» **mantienen su composición en tarjetas/bloques**. Esa variación es deliberada: rompe la monotonía de los tramos anteriores construidos con rails y columnas.

No deben reconvertirse a la composición lineal de Samuel o Eventos solo para homogeneizar la página. Se pueden corregir defectos objetivos de `padding`, separación, alineación o responsive, pero sin eliminar su carácter de bloque ni el destaque azul de «Lectores beta».

La composición mostrada de las tres obras se considera válida, incluidos los tres libros y sus acentos gráficos actuales.

## 4. Jerarquía cromática de los rótulos

El dorado con subrayado gráfico se reserva para los **rótulos de apertura de bloque/sección**, como «Obra actual», «Obras», «Universo publicado», «Para escribir» o «Agenda · Archivo».

Los rótulos internos de contenido —por ejemplo «Autor», «Comunidad», «Hub», «Lectores beta», «Manuscrito», «Publicada», «Antología», «Crónica» o «Comprar»— **permanecen neutros/grises**. No deben convertirse todos a dorado ni a azul.

## 5. Footer y «Volver arriba» en HOME

En la HOME, el footer y el control flotante «Volver arriba» deben utilizar los mismos acentos azul `#1d4f96` y dorado `#b8860b` del sistema visual de la página, manteniendo la estructura compartida del shell y sin introducir una tercera paleta.

## 6. Regla de trabajo

Durante esta migración se corrigen directamente errores objetivos de geometría, responsive, accesibilidad, estados de interacción, herencias CSS y restos inequívocos del sistema anterior.

Cuando una diferencia pueda ser una decisión visual deliberada —cambio de composición, tratamiento de una caja, eliminación de un énfasis, destino provisional de un CTA, etc.— debe consultarse antes de modificarla.
