# Amazon.es: afiliación, enlaces y presencia de autor — auditoría focalizada

**Corte:** 22-10-2026. **Estado:** investigación verificable en `main` + herramienta estática; cuenta privada y redirecciones Amazon **no verificadas**. No se ha abierto ninguna sesión de compra, realizado pedido ni lanzado CI.  
**Coordinación:** [#427 (cuenta Afiliados, aún abierta)](https://github.com/davidpd89/web-escritor/pull/427), [#396/#470 (Author Central ya configurado)](https://github.com/davidpd89/web-escritor/pull/470), [#476 (agrupación papel/Kindle resuelta el 09-09)](https://github.com/davidpd89/web-escritor/pull/476), [#683 (Creators API no elegible)](https://github.com/davidpd89/web-escritor/pull/683). No rehacer esas tareas.

## 1. Resultado concreto en el repositorio

| Superficie / fuente | Confirmado en código | Lo que **no** demuestra |
| --- | --- | --- |
| `data/reading-catalogue.json` | **55 fichas publicadas**, 55 búsquedas ISBN con `tag=davidporto-21`; **1** ficha con `url_amazon_afiliada` de producto directo (Coraline); **54** dependen de búsqueda ISBN. Coraline tiene **4** enlaces adicionales por formato. | Que Amazon devuelva el libro, la edición pretendida o una comisión. Una búsqueda ISBN es *fallback*, no producto verificado. |
| `scripts/build-reading-catalogue.py` | `amazon_destination` prioriza URL de producto; si falta usa búsqueda etiquetada. Botón y portada de ficha comparten destino; `rel=sponsored nofollow noopener noreferrer`. Validador comprueba forma y existencia de tag. | Que el tag coincida con una cuenta activa, ni que un ASIN distinto del declarado sea la edición correcta. |
| `data/reading-import-review.json` y `aviso-legal.html` | Declaran `davidporto-21`. El aviso legal contiene el texto de identificación exigido por Amazon. | Que ese ID siga autorizado, los sitios de tráfico estén registrados o los datos fiscales/pagos completos. |
| `index.html`, `libros/samuel-entre-mundos/index.html`, `autor.html` | Samuel enlaza a `amazon.es/dp/B0GB6LGQFH?tag=davidporto-21` con `rel=sponsored`. | Comisión/atribución real, disponibilidad y correspondencia comercial hoy. |
| `las-manecillas-del-recuerdo/index.html` y header común | Papel: `https://amzn.to/4zW6Yeu`; Kindle: `https://amzn.to/3SM4Oxu` (también en datos estructurados). Identificadores históricos: papel `B0HHY9MYLM`, Kindle `B0HHM71F46`; #476 documentó formatos agrupados el 09-09. | El `tag` ni destino final de los acortados **sin** verificación en cuenta/herramienta oficial. No confundir acortado con URL sin seguimiento. |
| Cinco plantillas muestreadas: Home, recomendaciones, Coraline, Samuel, Manecillas | El disclosure aparece en `aviso-legal.html` y hay `aria-label` de afiliación en varios botones; **no aparece texto visible de afiliación junto al enlace en esas plantillas**. #317 retiró deliberadamente las etiquetas visibles, después de #308. | Cumplimiento de la divulgación *junto al enlace* exigida actualmente; `aria-label` no sustituye una advertencia visual para todos. |

**Incidencia de calidad editorial de Coraline:** en `data/reading-catalogue.json` las cuatro `formatos_compra[].fuente_url` remiten al mismo producto de referencia, aunque los ASIN de los cuatro formatos difieren. El esquema exige una fuente HTTPS, **no** prueba que cada formato enlace al producto correcto. Revalidar ASIN/idioma/edición/formato antes de ofrecerlo como comprobado. No inventar ni sustituir ASIN por parecido de título.

La recopilación anterior es **estática, sobre el estado de `main` consultado**. No equivale a un rastreo exhaustivo de la página publicada en cada navegador. `scripts/audit-amazon-links.py` añade un escaneo local de HTML y catálogo *sin acceder a Amazon*; aún **no se ha ejecutado**.

## 2. Qué hacer primero (en este orden)

1. **Cuenta Afiliados (P0; acción autenticada, owner #427):** en [Central de Afiliados ES](https://afiliados.amazon.es/) verificar `account=active`, sitio `davidportodiaz.com` y redes aprobadas/registradas, identificación `davidporto-21`, avisos de política, estado de datos fiscales y pago (guardar únicamente `completo/pendiente`, nunca valores), país/es, ID secundarios y estado de elegibilidad de API. No afirmar ingresos por tener el tag en HTML. Amazon revisa solicitudes tras tres ventas aptas en 180 días.
2. **Seguimiento (P0):** con la sesión de Afiliados, usar el [Comprobador de enlaces y la asistencia de Amazon](https://afiliados.amazon.es/help/node/topic/G6253GFSARDQENZR) para URLs propias. Abrir *manualmente* los dos `amzn.to` y comprobar que llevan a **Manecillas papel/Kindle** con la asociación correcta; revisar Samuel y Coraline. El verificador oficial distingue URLs construidas manualmente de enlaces generados por Amazon. Un HTTP 200 o que un tag aparezca en URL **no acredita la atribución**. No generar clics, pedidos ni compras ficticias para probar.
3. **Transparencia (P0):** Amazon pide declaración visible **cerca del enlace**, además de identificación del sitio. El aviso legal ya está; la retirada de etiquetas visibles en #317 contradice esa precaución en las plantillas comprobadas. **Propuesta A:** nota editorial breve visible una vez en cada bloque de compra (sin repetir en cada botón). **Propuesta B:** «Enlace de afiliado» compacto en enlaces individuales. Validar con políticas actuales y el propietario antes de modificar la UI; no dar por cumplido solo con `aria-label`.
4. **Cobertura de catálogo (P1):** conservar búsquedas ISBN etiquetadas como *fallback* veraz. Sustituir búsquedas por enlaces producto **solo** al verificar ASIN + edición + idioma + formato + fecha/fuente. Priorizar las fichas con tráfico real; no generar 54 ASIN por inferencia o scraping no autorizado.
5. **Medición (P1, después de cuenta):** extraer de Amazon informes agregados 30/90 días de clics → pedidos → enviados → comisiones, por ID. Primero medir con `davidporto-21`; si el volumen justifica separar **web / catálogo / libros propios**, crear 1–3 Tracking IDs oficiales y actualizar links/generador de manera consistente, sin IDs por lector ni conversiones atribuidas al usuario individual. La analítica web mide clic de salida, Amazon mide ventas atribuidas; no se debe presentar una como prueba de la otra.

## 3. Dos perfiles distintos de Amazon: qué aporta cada uno

| Opción | Estado/función real | Decisión |
| --- | --- | --- |
| **Author Central / página de autor** | La web ya enlaza a [David Porto Díaz en Amazon.es](https://www.amazon.es/stores/author/B0GZFP1JV3); la auditoría autenticada #470 confirmó perfil, bio, foto y las obras añadidas. **Author Follow** permite a lectores seguir al autor y **puede** avisar de lanzamientos/preventas aptas; depende también de sus preferencias de Amazon. Se puede consultar el **total** de seguidores en Author Central; no mejora por sí solo el ranking de best sellers. | **Prioridad alta.** Revalidar hoy que Samuel y ambas ediciones de Manecillas aparecen y están agrupadas; añadir en web, ficha autor y libros un CTA discreto «Seguir al autor en Amazon» hacia la URL pública, **sin tag de afiliado** ni prometer avisos garantizados. Contar clics de salida agregados; consultar seguidores en cuenta, sin bots. |
| **Amazon Influencer Program / escaparate `amazon.es/shop/...`** | **Programa diferente** de Amazon Afiliados y de Author Central; necesita solicitud/aceptación basada en presencia social. Si Amazon aprueba, permite listas de ideas y escaparate con productos. No consta que exista un escaparate aprobado de David: **no inventar URL ni seguidores**. | **Condicional.** Solicitar solo si la cuenta social cumple sus criterios. Si se aprueba, crear una lista «Mis libros» (si las reglas/ASIN lo permiten) y otra «Lecturas que recomiendo», usando títulos que estén realmente en Amazon.es. Solo entonces decidir si enlazar escaparate desde recomendaciones o bio social. No confundir «seguir autor» con «seguidores de tienda». |
| **Contenido A+ en ficha de producto** | KDP permite módulos visuales para ASIN **gestionados por esa cuenta**, con aprobación por tienda. Samuel (Libros Indie) y Manecillas (Monza Ediciones) son ediciones editoriales: **no presumir control en el KDP personal**. | Preguntar a editorial/propietario de la ficha si tiene acceso y proponer A+ básico (imagen real, sinopsis original, universo/otras obras) en Amazon.es; hacerlo solo por quien controle los ASIN. No añadir datos falsos ni reseñas de compradores en A+. |
| **Amazon Advertising / KDP Select** | Canales distintos de Afiliados; dependen de titularidad y condiciones de distribución/exclusividad. | **No abrir tareas** sin acceso editorial, presupuesto y una hipótesis de rendimiento. Prioridad inferior a enlaces válidos y página de autor. |

**Conseguir seguidores de forma legítima:** desde `/autor.html`, fichas propias y perfiles de redes, enlazar al perfil real de Amazon con invitación específica a «Seguir»; dar contenido/obras interesantes y crear próximos lanzamientos correctamente en Author Central. No se conoce un mecanismo legítimo para «importar» seguidores de redes ni comprar seguidores Amazon. El recuento es consultable en la cuenta, pero no atribuye automáticamente cada seguidor al CTA web.

## 4. Entrega y criterios de salida

**Ya confirmado:** ID público consistente en el catálogo, 55 publicaciones con búsqueda afiliada, 1 producto directo en catálogo, 4 ASIN de Coraline por formato, 2 shortlinks propios, página de autor pública conocida, aviso legal con declaración. **No confirmado:** cuenta activa, titularidad del ID, pagos, ventas, saltos `amzn.to`, ASIN vigentes, exposición real en móvil, followers actuales, elegibilidad Influencer y A+.

**Checklist ejecutable al revisar con acceso autorizado (sin secretos):**
- [ ] Amazon Afiliados: cuenta/sitios/ID/impuestos/pagos y avisos, solo estados.
- [ ] Amazon Link Checker + inspección manual de shortlinks: ASIN/formato/tag registrado.
- [ ] Contrastar cada ASIN de Coraline con página de producto y fuente **del mismo formato**.
- [ ] Autor: dos libros + variantes, botón Seguir público, recuento interno de seguidores.
- [ ] Elegibilidad real de Influencer (sí/no); sin tienda ficticia.
- [ ] Disclosure visible junto al bloque de compra: solución A/B aprobada y revisada.
- [ ] Registrar baseline agregado y determinar si nuevos Tracking IDs aportan algo.
- [ ] Ejecutar localmente `python scripts/audit-amazon-links.py`, documentar incidencias; **no CI/Actions** hasta autorización.

**No cambiar aquí:** precios, productos, campañas, URLs de compra, CSS ni la arquitectura de #683. Esta PR aporta el diagnóstico actual y el comprobador offline, no un despliegue.

## Fuentes primarias consultadas (22-10-2026)

- [Amazon ES · políticas, actualización 14-04-2026](https://afiliados.amazon.es/help/operating/policies)
- [Amazon ES · formatos de enlaces y tag](https://afiliados.amazon.es/help/operating/linking) · [Comprobador de enlaces](https://afiliados.amazon.es/help/node/topic/G6253GFSARDQENZR)
- [Amazon ES · divulgación próxima al enlace](https://afiliados.amazon.es/help/node/topic/GHQNZAU6669EZS98)
- [Amazon ES · Tracking IDs](https://afiliados.amazon.es/help/node/topic/GK5TZZ4AWML2QSLA) · [Informes](https://afiliados.amazon.es/welcome/topic/reports) · [Revisión de solicitudes](https://afiliados.amazon.es/help/node/topic/G8TW5AE9XL2VX9VM)
- [KDP · Author Central y Author Follow, incluyendo seguidores](https://kdp.amazon.com/es_ES/help/topic/G200644310)
- [Amazon ES · qué es Influencer](https://afiliados.amazon.es/help/node/topic/GTP6NKQ2GXPZL7AT) · [Listas de ideas del escaparate](https://afiliados.amazon.es/help/node/topic/GU8CZSAGGW28CGMG)
- [KDP · Contenido A+](https://kdp.amazon.com/es_ES/help/topic/GHL7P99B7AA543CN) · [Solo ASIN de la biblioteca KDP propia](https://kdp.amazon.com/es_ES/help/topic/G8EP5W6H9CY7T8GS)
