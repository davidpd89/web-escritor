# K.4 · Merchandising mínimo viable

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `DEFER`.

## Veredicto

#135 dejó K.4 diferida: el merchandising no era una necesidad demostrada de la web ni del negocio. Antes de crear productos, tienda, stock o checkout debe existir demanda real y una operación capaz de servirla.

## Hipótesis original

La lista inicial planteaba validar mediante una encuesta simple productos mínimos —por ejemplo marcapáginas o pegatinas— antes de construir una tienda.

La parte correcta de la hipótesis era precisamente **validar antes de producir**.

## Evolución histórica

### Revisión 108/108 → `DEFER`

- valor bajo en el momento actual;
- coste operativo alto;
- no es una necesidad de la web;
- validar demanda antes de inventario.

### Matriz → `DEFERIR`

> «Merch: encuesta/demanda antes de tienda.»

### Autoridad final → `DEFER`

> «Merch solo tras demanda demostrada.»

La revalidación independiente mantuvo el estado del bloque K: no abrir comercio si no existe una oferta real.

## Estado actual de `main`

No se ha localizado una tienda de merchandising ni una autoridad de productos físicos en el repositorio actual. Las búsquedas por `merch`/bundle no devuelven una implementación específica.

Sí existen recursos visuales/editoriales de las obras y una vía manual de ejemplar firmado para Samuel. Ninguno de esos hechos demuestra que existan productos comercializables.

```text
promotional asset != merchandise product
book art != licensed merch by default
signed copy != merch catalog
```

## Trigger de reapertura

K.4 solo debería salir de `DEFER` si existe una señal suficientemente clara, por ejemplo:

- lectores preguntan repetidamente por un objeto concreto;
- evento/feria genera demanda observada;
- encuesta con muestra suficiente y pregunta útil;
- preventa/interés explícito sobre un producto ya definido;
- necesidad promocional/física concreta con presupuesto.

No reabrir por tendencia genérica de autores indie.

## Validación mínima

Antes de fabricar:

1. definir 1 producto concreto;
2. estimar coste, MOQ y margen;
3. comprobar derechos de arte/logos/textos;
4. medir interés sin recoger PII innecesaria;
5. fijar umbral `GO/NO-GO`;
6. decidir fulfillment;
7. producir solo tras superar el umbral.

La encuesta no debe preguntar veinte productos abstractos ni convertirse en una lista de deseos sin consecuencia.

## Productos de menor riesgo si algún día se valida

Por simplicidad operativa podrían evaluarse primero artículos planos/ligeros, por ejemplo:

- marcapáginas;
- postal/lámina;
- pegatina;
- print firmado.

Eso no significa que estén aprobados. Cada uno requiere coste, derechos, calidad y logística.

## Relación con K.2

Un bundle coleccionista puede incluir merch, pero K.2 no debe servir para saltarse el gate de K.4. Si no existe un producto real y validado, no puede formar parte de un paquete real.

## Relación con K.1

La operación de un libro firmado ya es suficiente complejidad logística. Añadir objetos físicos aumenta inventario, packaging, incidencias y soporte.

## Relación con diseño/branding

Los recursos gráficos del proyecto pueden inspirar producto, pero no deben producirse automáticamente a partir de assets web. Antes hay que revisar:

- resolución/uso de impresión;
- derechos de fuentes/imágenes;
- sangrado/color;
- permiso editorial cuando afecte a portadas;
- consistencia de marca.

## Qué NO hacer

- crear `/tienda/merch` vacía;
- mockups de IA presentados como stock real;
- fabricar varias referencias sin señal de demanda;
- comprar inventario para «tener algo que vender»;
- crear checkout antes de decidir fulfillment;
- añadir contador de unidades sin stock verificable;
- vender material con derechos no resueltos;
- asumir que seguidores/redes equivalen a compradores.

## Métricas si se valida

- número de respuestas cualificadas;
- intención sobre producto específico;
- conversión interés→compra si existe piloto;
- margen después de producción+envío+incidencias;
- carga operativa por pedido.

Likes/engagement no sustituyen intención de compra.

## Trazabilidad preservada

- hipótesis original de merch mínimo;
- validación por encuesta antes de tienda;
- revisión `DEFER`;
- matriz `DEFERIR`;
- autoridad final `DEFER`;
- revalidación independiente;
- relación con K.1/K.2 y derechos/stock.

## Recomendación para Clara/Claude

**No implementar merchandising ahora.** Si aparece demanda real, validar un único producto de bajo riesgo con umbral económico y de interés antes de tocar la arquitectura comercial de la web.