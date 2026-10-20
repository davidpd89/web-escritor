# PR #661: ingesta editorial y revisión del catálogo

## Comprobado localmente

- Piloto: 20 libros reales nuevos de ocho sellos, además de Coraline. Descubrimiento inicial de 158 enlaces; primera prueba de aceptación: 57 candidatos examinados, 20 aceptados y 37 pendientes. No se rellenó el cupo con datos inventados.
- Sellos: Alfaguara, Plaza & Janés, Grijalbo, Salamandra, Lumen, Reservoir Books, Ediciones B y Random House. El siguiente lote en previsualización aceptó cinco libros de Grijalbo y Roca Editorial.
- Carga final del piloto desde caché: cero solicitudes físicas, 43 respuestas reutilizadas. Cada ficha procede del producto editorial cuyo ISBN coincide con la URL y el registro.
- 40 pruebas offline: ISBN, fechas parciales, alias, ediciones, autores múltiples, cubiertas reales, clasificación, validación completa, candidato roto aislado, repetición sin duplicados, conservación de Coraline, actualización semanal y mantenimiento de fichas ante un cambio de autoría.
- Pruebas del publicador: todas las páginas de ficheros de la PR, renombrados, rama permitida, workflows reales, SHA exacto, ningún merge ante fallos o jobs omitidos. Reutilización del coordinador del radar sin saltar reglas de main.
- Navegador: 20 fichas, ocho editoriales, búsqueda por ISBN, enlaces de autores, Schema Book, cubiertas decodificables, mapa colapsado y teclado. Límite de Novedad: días 0/14/15, fecha futura y fecha parcial, medianoche de Madrid y cambio de horario de octubre.
- QA existente de catálogo y comercio: filtros combinados, cuatro tamaños, sin JavaScript, texto ampliado/espaciado, formatos, precios y descuentos asociados, valoraciones, caducidad, fuentes inválidas y conservación de UTM.
- Revisión visual móvil: portada real grande, tipografía común, rótulo Novedad en dorado manuscrito, reglas azules/doradas, botón azul y acordeones nativos.

## Correcciones encontradas durante la revisión

1. La fuente repite el campo Autor: se conservaban únicamente los datos del último coautor. Se extraen todos los campos y se deduplican sin perder coautorías.
2. El importador de Drive reconstruía solo sus libros y habría descartado los automáticos. Ahora conserva entradas con registro de ingesta y sus categorías.
3. Varias pruebas estaban fijadas a un único libro real. Ahora contrastan el total del dataset y mantienen fixtures aisladas para sus casos específicos.
4. Las nuevas fichas no tenían género cuando la materia era biografía, cocina, familia, autoayuda o aventuras. Se mapean las materias explícitas sin inferirlas del título.
5. El flujo automático necesita disparar CI y Pages explícitamente y conservar el SHA anterior para IndexNow. Se comprueban jobs reales y el despliegue exacto.

## Límites y servicios opcionales

La fuente actual es Penguin Libros España, no todas las editoriales ni todas las altas de Amazon. Sin ASIN verificado se ofrece búsqueda afiliada por ISBN. No hay proveedor automático de precios o estrellas; las búsquedas de Goodreads no son reseñas importadas. El proveedor de Elvira rechazó las nuevas narraciones; queda desactivado y Coraline conserva su MP3. No se copian ni narran capítulos ajenos. No se publican pines desde esta tarea.

## CI, despliegue y primera ejecución autónoma

Pendientes de registrar tras la validación y publicación de la rama. No se considera demostrada la publicación automática hasta observar un lote creado por Actions, validado, fusionado y desplegado.
