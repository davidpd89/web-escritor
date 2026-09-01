# D.2 · Modo lectura dedicado para el Cuaderno

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## 1. Hipótesis original

Crear una vista propia «reader mode» para artículos largos: solo texto, tipografía ampliable, ancho de línea controlado y menos distracciones, independientemente del Reader Mode del navegador.

## 2. Evolución de la decisión

### Revisión 108/108 → `REJECT`

#135 detecta que la necesidad principal no es otro modo de interfaz, sino una buena experiencia de lectura base y responsive. Mantener un Reader Mode propio multiplica estados y duplica capacidades nativas.

### Matriz intermedia → `DEFERIR`

La matriz suaviza temporalmente el rechazo:

> «Un “reader mode” propio duplica capacidades del navegador y añade mantenimiento. Mejorar tipografía/composición base primero.»

### Autoridad final → `REJECT`

El cierre vuelve a un veredicto explícito:

> «Reader mode propio duplica navegador y añade estados; primero mejorar composición/lectura base.»

### Revalidación independiente

La revalidación menciona expresamente que Reader Mode, hover previews y share-selection no compensan.

## 3. Problema de producto

Un modo paralelo implicaría mantener, como mínimo:

- layout normal;
- layout reader;
- desktop/móvil de ambos;
- zoom/text spacing de ambos;
- light/dark si D.8 algún día cambiara;
- navegación/foco;
- impresión;
- imágenes/captions;
- embeds;
- analytics y deep links.

Ese coste solo tiene sentido si la composición normal no puede satisfacer lectura accesible, lo que sería un defecto de la base.

## 4. Principio preservado

La página normal debe ser legible sin activar un modo especial:

- medida de línea razonable;
- interlineado adecuado;
- tipografía estable;
- reflow a 320px;
- zoom/text spacing sin pérdida;
- jerarquía clara;
- navegación no invasiva;
- movimiento reducido;
- foco visible;
- no sticky UI excesiva.

Un modo alternativo no debe tapar fallos de estas condiciones.

## 5. Relación con accesibilidad

F.5 llegó a una conclusión análoga para «texto grande»: no crear controles propios si el objetivo correcto es soportar correctamente zoom/ajustes nativos hasta 200%.

D.2 y F.5 comparten una regla:

```text
robustez de la experiencia base
> multiplicar modos de presentación propios
```

## 6. Relación con D.8

D.8 difiere un dark-mode manual por la misma razón de coste de estados. Combinar Reader Mode + Dark Mode + texto grande generaría una matriz de combinaciones difícil de mantener.

No usar D.2 como puerta lateral para implementar D.8/F.5.

## 7. Relación con D.3 y D.9

D.3 (progreso) y D.9 (tiempo estimado) son ayudas pequeñas que pueden vivir sobre la lectura normal si demuestran utilidad. No necesitan un Reader Mode.

## 8. Browser-native Reader Mode

La idea original pretendía independencia del navegador. #135 concluye que esa independencia no justifica el mantenimiento adicional.

La web debe usar HTML semántico y estructura editorial suficientemente limpia para que:

- lectores de pantalla;
- browsers;
- modos de lectura nativos;
- herramientas de accesibilidad

puedan interpretar el contenido sin una copia paralela del artículo.

## 9. Riesgos de una implementación propia

- contenido duplicado o DOM alternativo divergente;
- anchors/deep links que dejan de funcionar;
- imágenes/captions omitidos;
- pérdida de navegación esencial;
- errores de foco al activar/desactivar;
- estado persistido no esperado;
- bugs con back/forward;
- diferencias de canonical/metadata si se crea otra URL;
- QA multiplicado;
- falsa sensación de accesibilidad.

## 10. Qué NO hacer

- `/reader/` o `?reader=1` indexables;
- duplicar artículos en plantillas simplificadas;
- esconder navegación sin ofrecer salida clara;
- meter controles de tamaño/color como bundle de Reader Mode;
- afirmar que mejora SEO o engagement sin evidencia;
- sustituir correcciones de CSS/editorial por un toggle.

## 11. Qué hacer en su lugar

Prioridad:

1. medir legibilidad/reflow real de artículos largos;
2. corregir ancho, ritmo, headings y spacing en la plantilla principal;
3. asegurar `font-size:200%` y Text Spacing;
4. auditar sticky elements/focus;
5. permitir que capacidades nativas funcionen;
6. solo reabrir D.2 si una necesidad de usuario concreta no puede resolverse en la base.

## 12. Gate extraordinario de reapertura

Aunque el estado final es `REJECT`, podría revisarse en el futuro solo con evidencia fuerte:

- investigación de usuarios muestra una necesidad repetida;
- browsers objetivo no cubren el caso;
- la solución no duplica contenido ni rompe deep links;
- existe un owner de QA de los estados adicionales;
- beneficio medido supera coste.

No reabrir por tendencia de diseño.

## 13. Pasadas posteriores revisadas

Cuarta–decimoquinta: no añaden un override que rehabilite Reader Mode. R.13 `prefers-contrast` propone adaptar mínimamente la base según preferencias del sistema, reforzando la estrategia de respetar capacidades nativas en vez de crear otro tema/modo.

## 14. Trazabilidad

- lista inicial — modo lectura dedicado;
- revisión — `REJECT`;
- matriz — `DEFERIR`;
- autoridad final — `REJECT`;
- revalidación independiente — rechazo mantenido;
- F.5/R.13 — evidencia transversal a favor de robustez base/preferencias nativas.

## 15. Definition of Done de esta reconstrucción

- [x] rechazo original/final preservado;
- [x] `DEFERIR` intermedio preservado;
- [x] coste de estados explicitado;
- [x] relación con F.5/D.8 separada;
- [x] alternativa correcta documentada;
- [x] sin implementación de runtime.

## Recomendación para Clara/Claude

No implementar Reader Mode propio. Mejorar y probar la experiencia editorial normal; reabrir solo si investigación real demuestra una necesidad que la base y el navegador no resuelven.