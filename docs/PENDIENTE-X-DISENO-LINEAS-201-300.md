# X — Diseño final · líneas 201–300

Fuente auditada: `PENDIENTE DISEÑO GPT.txt`, líneas **201–300 exactas**.
Base contrastada: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

> Este documento no interpreta la línea 301 ni contenido posterior.

## Resultado

Este bloque **no abre una nueva PR de diseño**. Refuerza y amplía el owner de #83 para media/procedencia/color y confirma que el resto del inventario/migración está mayoritariamente cerrado.

## Elementos ya absorbidos / sin nueva deuda de diseño

- Shortcuts y utilidad `site-map` de Explorar → owner funcional #68; no duplicar aquí.
- View Transitions, hero reveal, rutas y preview visual → #82.
- Accesibilidad pública y retirada de `aria-live` del preview → ya resuelto en el repo real.
- «Esta web, en cifras» → owner funcional #81; no pertenece al diseño final.
- Gate temporal de Manecillas → release/editorial, no diseño.
- Cartografía hover/focus y asistente no autoabierto → ya corregidos históricamente.
- Back to top aparece en la línea 297, pero su especificación continúa después de la 300: **no se interpreta todavía en este bloque**.

## Evidencia externa `hoymadrid.app`

Las líneas 251–259 recuerdan una posible recuperación de evidencia editorial externa. No es un requisito de diseño visual y por tanto no genera PR nueva aquí. Si al cierre funcional sigue sin owner, debe tratarse como evidencia/contenido verificado, nunca como motivo para insertar un enlace arbitrario en footer o UI.

## X.1 ampliado por el Media System / documento 30

Las líneas 264–281 confirman que el simple hecho de tener imágenes en `/assets/` no cierra el gobierno de media. El contrato de #83 debe incluir también, cuando corresponda, los campos/semántica del Media System V1:

- **función M1–M7** o taxonomía equivalente de función visual;
- procedencia;
- derechos y **publicabilidad**;
- crops permitidos/derivados;
- dimensiones intrínsecas o referencia al dato técnico canónico;
- caption/alt/copy editorial cuando aplique;
- territorio visual;
- superficies/usos autorizados;
- relación entre fuente y derivados.

Por tanto, el futuro manifest no puede limitarse a `sourceAsset + rightsStatus + colorExtraction`: debe poder gobernar el uso editorial real de la pieza.

## Paridad y gate de CI

Antes de producción debe existir una comprobación reproducible que detecte al menos:

1. asset de identidad/producción usado sin entrada de gobierno cuando el contrato exige registro;
2. `productionAsset` o `sourceAsset` local inexistente;
3. estados de derechos/publicabilidad inválidos;
4. pieza declarada publicable con derechos todavía `unknown/pending`, salvo excepción explícita y documentada;
5. crop/derivado que no trace a una fuente cuando debería hacerlo;
6. tokens cromáticos declarados como derivados sin muestras/fuente;
7. divergencia entre media utilizada por las superficies finales críticas y el inventario final.

El checker no debe tratar como error cualquier icono/ornamento trivial: el alcance debe centrarse en assets de identidad, editoriales, documentales y de producción relevantes.

## Corrección de autoridad sobre IA/generación

Las líneas 266–277 reflejan una decisión histórica anterior que decía que la generación de imágenes IA para V1 estaba descartada. **Esa regla queda superada por la decisión explícita posterior del propietario durante esta auditoría de diseño.**

Regla vigente:

- sí se permiten piezas generadas, retocadas o reconstruidas cuando solucionen una necesidad real de diseño;
- se pueden extraer JSON/especificaciones de imágenes/referencias reales y adaptar el lenguaje visual al proyecto;
- se pueden producir fondos, abstracciones, texturas, composiciones y recursos visuales propios;
- se prioriza material real cuando tenga valor documental o identitario;
- se evita la estética IA genérica y se prohíbe presentar material inventado como evidencia documental real;
- la procedencia/derivación debe quedar bien etiquetada en #83.

No se rescata automáticamente ningún banco antiguo de prompts P1–P6/A–H: pueden reutilizarse ideas puntuales únicamente si encajan con la dirección final y se rehacen deliberadamente.

## Relación con #82

#83 prepara la materia prima gobernada; #82 decide cómo se usa visualmente en Home/cartografía.

Orden recomendado:

1. #83 define/implementa schema, inventario inicial y extracción cromática.
2. #82 consume esa autoridad al aplicar materialidad, previews y fondos.
3. #78 valida responsive/resiliencia sobre la implementación acumulada.
4. Release final valida paridad/media/performance sobre HEAD integrado.

## Estado

No se crea PR nueva para 201–300. Este archivo amplía **#83**.

No se toca `main`, no hay deploy y no hay auto-merge.
