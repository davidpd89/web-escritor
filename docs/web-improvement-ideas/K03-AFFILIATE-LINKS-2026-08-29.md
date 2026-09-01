# K.3 · Afiliación con librerías / retailers

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.

## Veredicto

#135 no aprobó una expansión general de afiliación. La dejó condicionada a programas reales, URLs verificadas, disclosure y marcado adecuado. La web no debe convertir cada recomendación o retailer en una oportunidad de comisión ni inventar relaciones comerciales.

## Hipótesis original

Añadir enlaces de afiliado a librerías/tiendas donde se venden los libros, siempre que la relación comercial exista y se declare.

## Evolución histórica

### Revisión 108/108 → `CONDITIONAL`

- solo afiliaciones reales;
- disclosure;
- `rel=sponsored` cuando corresponda;
- no inventar programas;
- Samuel ya tenía una relación Amazon identificable.

### Matriz → `CONDICIONAL`

> afiliación únicamente con programa real, disclosure y URLs válidas; no convertir todas las recomendaciones en affiliate pages.

### Autoridad final → `CONDITIONAL`

> «Afiliación solo con programa real, disclosure y URLs verificadas.»

La revalidación independiente mantuvo K.1–K.5: comercio/afiliación solo con relaciones y ofertas reales.

## Estado actual de `main`

La página de *Samuel entre mundos* contiene una implementación real y específica de Amazon:

```text
https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21
rel="sponsored nofollow noopener noreferrer"
```

Aparece tanto en el CTA de compra como en enlaces relacionados. Esto demuestra que K.3 **no parte de cero** y que existe al menos un programa concreto.

Sin embargo:

- Casa del Libro aparece sin afiliación declarada;
- Libros Indie aparece como editorial, no como programa de afiliación;
- no debe inferirse que cualquier retailer soporte comisión;
- un `sameAs` factual no debe convertirse en enlace patrocinado por defecto.

## Trigger para ampliar K.3

Cada nuevo retailer/programa debe superar individualmente:

1. cuenta/programa real y activo;
2. términos compatibles con la promoción prevista;
3. URL/código válido;
4. relación comercial vigente;
5. disclosure visible adecuado;
6. `rel=sponsored` en enlaces pagados/afiliados;
7. destino correcto y disponible;
8. medición proporcional, sin tracker adicional innecesario.

## Modelo recomendado

La autoridad debería distinguir explícitamente:

```text
retailer
book
public_url
affiliate = true|false
affiliate_program
tracking_parameter
relationship_verified_at
disclosure_required
rel_policy
status
```

No mezclar “dónde comprar” con “afiliación”. Una tienda puede ser un destino factual sin generar comisión.

## Disclosure

El usuario debe poder entender que ciertos enlaces pueden generar comisión. No esconder la relación exclusivamente en `rel=sponsored`, porque ese atributo es técnico y no sustituye información visible cuando corresponda.

El texto exacto debe ser factual y proporcional; no hace falta contaminar cada CTA si existe una explicación clara y accesible en la superficie adecuada.

## SEO

- `rel=sponsored` es la señal correcta para enlaces de naturaleza patrocinada/comercial;
- no usar afiliación como estrategia de link building;
- no crear thin affiliate pages;
- no copiar fichas/sinopsis de retailers;
- la página propia debe conservar valor editorial original.

## Books2Read — hallazgo adicional de #135

La investigación final detectó Books2Read UBL como oportunidad **condicional** cuando existan ebook y/o múltiples retailers compatibles.

Reglas preservadas:

- pilotar primero en social/email;
- no sustituir enlaces canónicos de compra sin comprobar atribución y utilidad;
- revisar códigos de afiliación/condiciones;
- no presentarlo como una “idea 109” separada del sistema de distribución.

En el estado actual no existe evidencia suficiente para convertir Books2Read en una obligación de K.3.

## Relación con K.1

La venta directa y la afiliación son modelos distintos. Un enlace afiliado puede reducir carga operativa precisamente porque el retailer gestiona pago/envío. No debe mezclarse con la solicitud manual de ejemplares firmados.

## Relación con recomendaciones

No convertir el Cuaderno o las recomendaciones en un catálogo monetizado por defecto. Si alguna recomendación usa afiliación:

- criterio editorial independiente;
- relación declarada;
- no alterar la selección por comisión;
- enlaces no afiliados cuando no exista programa real.

## QA futuro

- URL responde y lleva al producto correcto;
- tracking parameter pertenece al programa real;
- `rel=sponsored` presente cuando corresponda;
- `noopener noreferrer` para targets externos según contrato actual;
- disclosure visible y accesible;
- no datos falsos de precio/disponibilidad;
- no schema `Offer` si el sitio no es el vendedor o no dispone de datos verificables.

## Qué NO hacer

- añadir tags de afiliado no autorizados;
- inventar programa de Casa del Libro/editorial;
- sustituir todos los enlaces externos por monetizados;
- ocultar la relación comercial;
- crear páginas long-tail para captar clic afiliado;
- afirmar precios o stock sin fuente operativa;
- instalar otro tracker solo para comisión si el programa ya ofrece reporting.

## Trazabilidad preservada

- hipótesis original;
- revisión `CONDITIONAL`;
- matriz `CONDICIONAL`;
- autoridad final `CONDITIONAL`;
- evidencia de Amazon affiliate ya presente en Samuel;
- política `rel=sponsored`;
- oportunidad Books2Read condicional;
- revalidación independiente.

## Recomendación para Clara/Claude

**Mantener el Amazon affiliate existente de Samuel mientras siga siendo válido y correctamente declarado.** Ampliar retailer por retailer únicamente cuando exista un programa real y verificable. No convertir K.3 en una estrategia sitewide de monetización.