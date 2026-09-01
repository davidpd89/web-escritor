# N.2 · Open Graph/Twitter metadata localizados solo con contenido alternativo real

Fecha de reconstrucción: 2026-08-29  
Fuente: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `DEFER`.

## Veredicto

`og:locale=es_ES` ya cubre correctamente el idioma social actual. `og:locale:alternate` o tarjetas en otro idioma solo deben añadirse cuando existan páginas alternativas reales y útiles.

## Hipótesis original

Confirmar `og:locale` y evaluar alternates de cara a futura expansión internacional.

## Evolución

- revisión: `DEFER`/ya cubierto en español;
- matriz: `YA_CUBIERTO/DEFERIR`;
- autoridad final: `DEFER`;
- revalidación independiente: sin cambio.

La transición importa: comprobar `es_ES` era una auditoría válida; publicar alternates hipotéticos no lo es.

## Revalidación actual

Las páginas actuales inspeccionadas declaran `og:locale="es_ES"`. No existe una familia pública equivalente en inglés u otro idioma. Por tanto:

```text
og:locale es_ES = cubierto
og:locale:alternate = no aplicable todavía
localized Twitter/OG copy = no publicar sin versión real
```

## Relación con N.1/C.9/G.4

- N.1 difiere `hreflang` hasta traducciones reales;
- C.9 difiere el proyecto internacional hasta derechos/idioma/calendario reales;
- G.4 rechaza metadata inglesa generada por IA sin contenido internacional real.

N.2 no puede convertirse en vía lateral para saltarse esas decisiones.

## Trigger futuro

Solo reabrir alternates si existe:

- URL pública equivalente;
- idioma/locale real;
- copy social revisado en ese idioma;
- imagen/card adecuada si difiere;
- canonical/hreflang coherentes;
- relación recíproca entre versiones.

## Qué NO hacer

- declarar `og:locale:alternate=en_US` por intención futura;
- traducir solo title/description mientras el cuerpo sigue en español;
- generar tarjetas inglesas con IA sin versión inglesa;
- usar alternates como supuesto boost internacional;
- duplicar metadatos contradictorios con `lang`/canonical.

## QA futuro

- `lang`, `og:locale`, hreflang y contenido se corresponden;
- alternates apuntan a páginas reales;
- OG/Twitter cards tienen copy e imagen coherentes;
- no hay URL alternativa noindex/404;
- social debugger no revela drift de canonical.

## Trazabilidad

- backlog N.2;
- revisión 108/108;
- matriz `YA_CUBIERTO/DEFERIR`;
- autoridad final `DEFER`;
- revalidación independiente;
- relación con N.1/C.9/G.4.

## Recomendación

Mantener `es_ES`. No añadir `og:locale:alternate` hasta que exista una versión lingüística real de la página.