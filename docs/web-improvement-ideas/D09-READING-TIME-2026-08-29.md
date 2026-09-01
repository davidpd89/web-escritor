# D.9 · Indicador de tiempo de lectura estimado

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.  
Revalidación actual: no se ha localizado una implementación sitewide equivalente en `main`; sigue siendo opcional, no deuda automática.

## 1. Hipótesis original

Mostrar minutos estimados de lectura en artículos del Cuaderno y, en la formulación inicial, también en obras.

La idea partía de una convención editorial frecuente, pero #135 separó rápidamente utilidad humana de cualquier supuesto beneficio SEO.

## 2. Evolución histórica

### Revisión → `CONDITIONAL`

#135 limita el alcance:

- puede aportar en piezas largas de Cuaderno;
- calcularlo de forma determinista en build;
- documentar la regla;
- **no ponerlo en fichas de libros**;
- no venderlo como factor SEO.

### Matriz → `PILOTAR BAJO COSTE`

> «Tiempo de lectura generado al build en Cuaderno, si no recarga cabeceras. No es factor SEO.»

La matriz propone un piloto pequeño, no un componente global.

### Autoridad final → `CONDITIONAL`

> «Tiempo de lectura puede generarse en build si no ensucia cabecera. No es factor SEO.»

### Revalidación independiente

D.1–D.12 se mantienen sin elevar D.9.

## 3. Problema que puede resolver

Para una pieza larga, «8 min de lectura» puede ayudar a decidir:

- leer ahora;
- guardar enlace para después;
- entender la longitud aproximada.

En una pieza corta o ficha de producto, añade ruido.

La pregunta correcta es editorial: **¿la expectativa de duración ayuda al lector en esta familia?**

## 4. Build-time, no runtime

Si se implementa, #135 favorece cálculo en build.

Ventajas:

- cero JS adicional;
- valor estable en HTML;
- no recalcular en cliente;
- accesible como texto normal;
- fácil de verificar/testear;
- no afecta INP.

## 5. Regla de cálculo

Debe ser explícita y estable.

Ejemplo conceptual:

```text
words = texto editorial elegible
wpm = constante documentada
minutes = max(1, round(words / wpm))
```

La constante concreta debe decidirse una vez y testearse; no cambiarla para producir números «más bonitos».

## 6. Qué texto contar

No contar indiscriminadamente todo el HTML.

Excluir cuando corresponda:

- navegación;
- footer;
- diálogo Explorar;
- newsletter;
- related cards;
- JSON-LD;
- alt text;
- scripts/styles;
- chrome repetido.

Contar el cuerpo editorial principal.

Si una página contiene tablas/listas significativas, la estimación puede ser menos exacta; sigue siendo una **estimación**, no tiempo prometido.

## 7. Redondeo y copy

Copy recomendado:

```text
≈ 8 min de lectura
```

o

```text
8 min de lectura
```

si el diseño ya hace obvio que es aproximado.

No usar precisión falsa como «7 min 32 s».

## 8. Dónde sí / dónde no

### Candidatos

- artículos largos de Cuaderno;
- guías/editoriales extensas si research confirma utilidad.

### No por defecto

- ficha de libro;
- Home;
- herramientas;
- páginas legales;
- prensa;
- fragmentos literarios, salvo decisión editorial específica.

La primera hipótesis incluía «cada obra»; la revisión de #135 descarta ese alcance.

## 9. Cabecera editorial

El estado final exige no ensuciar cabeceras. Si existe mucha metadata (fecha, categoría, autor, revisión, etc.), añadir otro badge puede empeorar jerarquía.

Antes de mostrar:

- revisar composición móvil;
- priorizar metadata realmente útil;
- no crear fila de chips por consistencia.

## 10. SEO

No existe base en #135 para tratar tiempo de lectura como factor de ranking.

No añadir schema inventado ni claims tipo:

- «mejora dwell time»;
- «Google premia reading time»;
- «aumenta E-E-A-T».

Es UX editorial.

## 11. Relación con D.3

D.9 = expectativa previa.  
D.3 = progreso durante la lectura.

Pueden coexistir, pero no son un paquete obligatorio. D.3 ya existe parcialmente; D.9 no debe añadirse para «completar» el patrón.

## 12. Relación con D.4

Un usuario podría decidir guardar una pieza larga después de ver la duración, pero D.4 sigue condicionada a demanda. D.9 no crea esa demanda.

## 13. Accesibilidad

Es texto informativo simple:

- no necesita ARIA especial;
- no debe ocultarse solo en tooltip;
- debe reflow correctamente;
- evitar icono sin label;
- contraste adecuado.

## 14. Testing si se implementa

- fixture con recuento conocido;
- exclusión de chrome;
- resultado determinista;
- mínimo de 1 minuto si se decide ese contrato;
- no se muestra en familias excluidas;
- builder/check detecta output stale si se deriva a HTML generado;
- mobile/reflow de metadata.

## 15. Qué NO hacer

- calcular en JS en cada carga;
- contar todo `document.body.innerText`;
- mostrar en fichas de libros por defecto;
- precisión de segundos;
- usarlo como señal SEO;
- añadir dependencia npm para una división simple;
- duplicar contadores si una autoridad de contenido ya conoce word count.

## 16. Trigger de implementación

```text
long-form family
AND metadata hierarchy has room
AND user/editorial value > visual noise
AND build-time derivation can reuse existing authority
```

## 17. Pasadas posteriores revisadas

Cuarta–decimoquinta no cambian D.9. Las investigaciones de CWV/INP apoyan el enfoque build-time; ninguna fuente posterior convierte reading time en factor SEO o requisito de UX.

## 18. Trazabilidad

- lista inicial — tiempo estimado en artículos/obras;
- revisión — `CONDITIONAL`, limitado a Cuaderno largo;
- matriz — `PILOTAR BAJO COSTE`;
- autoridad final — `CONDITIONAL`;
- revalidación independiente — mantenida;
- repo actual — sin implementación equivalente localizada.

## 19. Definition of Done de esta reconstrucción

- [x] alcance original y reducción posterior preservados;
- [x] build-time como arquitectura preferida;
- [x] no-factor-SEO explicitado;
- [x] relación con D.3/D.4 separada;
- [x] gate editorial/visual documentado;
- [x] sin implementación prematura.

## Recomendación para Clara/Claude

Mantener D.9 condicionada. Si se pilota, hacerlo solo en Cuaderno long-form, calculado en build y después de comprobar que mejora la orientación sin saturar la cabecera.