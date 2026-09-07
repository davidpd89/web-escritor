# Amazon Author Central — paquete final de ejecución

Fecha: **2026-09-07**  
PR: **#396**  
Estado: **RESEARCHED · READY_FOR_AUTHENTICATED_EXECUTION**

Este suplemento actualiza y concreta el runbook principal. Si existe una discrepancia con `amazon-author-central.md`, prevalece este documento para el estado factual de 2026-09-07.

## 1. Resultado que buscamos

Una única identidad pública de **David Porto Díaz** en Amazon.es, con `Samuel entre mundos` y las dos ediciones reales de `Las manecillas del recuerdo` correctamente asociadas, sin duplicados ni datos inventados.

El objetivo no es tocar KDP ni crear productos nuevos. Author Central se usa para **perfil + asociación autor↔libro**; los metadatos editoriales que no controle David se escalan a Amazon/Monza/Libros Indie según corresponda.

## 2. Datos canónicos listos para copiar/comparar

### Autor

- Nombre: **David Porto Díaz**
- Web oficial: `https://davidportodiaz.com/`
- Author Page pública registrada: `https://www.amazon.es/stores/author/B0GZFP1JV3`
- Amazon author ID esperado: `B0GZFP1JV3`
- ORCID: `0009-0005-9089-3782`
- Goodreads: `https://www.goodreads.com/author/show/66843136.David_Porto_D_az`

### Samuel entre mundos

- Título: **Samuel entre mundos**
- Autor: **David Porto Díaz**
- Editorial: **Libros Indie**
- Formato conocido: **Paperback / tapa blanda**
- ISBN-13: `9791387659776`
- ASIN Amazon usado actualmente por la web: `B0GB6LGQFH`
- Páginas: `422`
- Publicación: `2025`
- No crear una edición Kindle/ebook inexistente.

### Las manecillas del recuerdo — papel

- Título: **Las manecillas del recuerdo**
- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- Formato: **Paperback / tapa blanda**
- ISBN-13: `9798905149351`
- ISBN con guiones: `979-8-90514-935-1`
- ASIN Amazon: `B0HHY9MYLM`
- Publicación: `2026-09-03`
- Páginas: `272`
- PVP actual documentado por el sitio/Amazon: **15,99 €**
- URL Amazon directa: `https://www.amazon.es/dp/B0HHY9MYLM`
- Shortlink actual: `https://amzn.to/4zW6Yeu`

**Corrección importante:** el runbook original de #396 todavía contiene una línea antigua con `16 €`. El valor vigente usado por la web es **15,99 €**. No usar `16 €` al rellenar ningún campo.

### Las manecillas del recuerdo — Kindle

- Título: **Las manecillas del recuerdo**
- Autor: **David Porto Díaz**
- Editorial: **Monza Ediciones**
- Formato: **Kindle / ebook**
- ASIN: `B0HHM71F46`
- ISBN-13: `9798906781925`
- Publicación: `2026-08-12`
- PVP actual documentado: **2,99 €**
- URL Amazon directa: `https://www.amazon.es/dp/B0HHM71F46`
- Shortlink actual: `https://amzn.to/3SM4Oxu`

No copiar a Kindle las 272 páginas de papel. La web trata las dos ediciones como manifestaciones distintas.

## 3. Estado del repo ya comprobado

No hace falta modificar ahora mismo la web para “dar de alta” Author Central:

- `autor.html` ya incluye `https://www.amazon.es/stores/author/B0GZFP1JV3` en `Person.sameAs`;
- la ficha de Manecillas ya distingue papel `15.99` / Kindle `2.99` en JSON-LD;
- los CTA actuales separan físico (`4zW6Yeu`) y Kindle (`3SM4Oxu`).

Por tanto, **NO_CODE_CHANGE_REQUIRED_BEFORE_EXTERNAL_AUDIT**.

Solo tocar código si la sesión autenticada demuestra que el author ID público canónico es otro o que Amazon entrega una URL definitiva distinta. Si no cambia el ID, no hacer churn en el repo.

## 4. Biografía preparada

Versión recomendada, factual y suficientemente corta:

> David Porto Díaz es un escritor español nacido en Pontevedra y residente en Madrid. Es autor de *Las manecillas del recuerdo* (Monza Ediciones, 2026), novela coral sobre memoria, familia y los objetos que heredamos, y de *Samuel entre mundos* (Libros Indie, 2025), novela de fantasía juvenil ambientada en Noveris. En 2026 obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue finalista del I Premio de Literatura Infantil Juan Andrés Teno. Más información en davidportodiaz.com.

No añadir ventas, rankings, número de reseñas, estrellas, “bestseller”, KU ni otros claims volátiles/no confirmados.

Antes de guardar, comparar con la bio existente: si la actual ya contiene toda la información correcta y es mejor, conservarla.

## 5. Foto preparada

Usar la fotografía canónica actual del sitio/kit de prensa. No generar una imagen nueva para Amazon.

Criterio:

- si la foto actual de Author Central ya es la misma/correcta y tiene calidad suficiente → `NO_ACTION`;
- si es vieja, incorrecta o de baja calidad → sustituir por la foto canónica del proyecto con derechos claros.

## 6. Capacidad actual de Author Central verificada en documentación oficial

A fecha 2026-09-07, la ayuda oficial de Amazon/KDP mantiene Author Central para Amazon.es y documenta que permite:

- añadir libros al perfil;
- editar biografía del autor;
- añadir imagen del perfil;
- revisar catálogo, rankings/reseñas y seguidores;
- aprovechar el ecosistema **Author Follow** cuando Amazon lo ofrece.

El botón `Seguir` puede ayudar a que seguidores reciban avisos de nuevos lanzamientos elegibles; no prometer que todos reciben notificación ni que influye en el ranking.

Fuentes primarias:

- `https://kdp.amazon.com/es_ES/help/topic/G200644310`
- `https://kdp.amazon.com/es_ES/help/topic/G201499010`
- `https://kdp.amazon.com/es_ES/help/topic/G2BWJN2BY98T5PV2`
- `https://kdp.amazon.com/es_ES/help/topic/G200736410`

## 7. Orden exacto para Claude

### A. Entrar y comprobar ownership

1. Abrir Author Central en la cuenta ya autenticada.
2. Confirmar que la página gestionada corresponde a `B0GZFP1JV3`.
3. Buscar posibles perfiles duplicados por:
   - `David Porto Díaz`
   - `David Porto Diaz`
   - `David Porto`
4. No crear una segunda página si existe una recuperable.

Resultado esperado: `AUTHOR_PAGE_CLAIMED` o dependencia claramente registrada.

### B. Perfil

1. Comparar nombre.
2. Comparar foto.
3. Comparar bio.
4. Confirmar web oficial si la interfaz actual ofrece ese campo.
5. Eliminar cualquier formulación “próximamente” o “próxima novela” para Manecillas si aún existiera.
6. Revisar la vista pública anónima después de guardar.

### C. Añadir/revisar libros

Usar identificadores exactos, en este orden:

1. Samuel: `9791387659776` / `B0GB6LGQFH`
2. Manecillas Kindle: `B0HHM71F46`
3. Manecillas papel: `B0HHY9MYLM`

Para cada resultado comprobar portada + autor + edición antes de pulsar “Añadir este libro”.

### D. Vinculación papel/Kindle

Comprobar si Amazon presenta ambas ediciones de Manecillas como formatos de la misma obra.

Si están separadas:

1. confirmar título exacto;
2. confirmar autor exacto;
3. confirmar publisher/editorial;
4. confirmar que ambas están asociadas al author page;
5. determinar ownership;
6. si David no controla los metadatos, preparar incidencia para Monza/Amazon con ambos ASIN.

No crear otra edición ni volver a publicar el libro para forzar la unión.

### E. Duplicados

Buscar por título, ISBN y ASIN. Registrar únicamente duplicados reales. No fusionar registros solo porque se parezcan.

### F. QA final

Verificar en sesión pública/anónima:

- escritorio;
- móvil;
- nombre/foto/bio;
- Samuel visible y navegable;
- Manecillas papel visible;
- Manecillas Kindle visible;
- formatos agrupados o incidencia registrada;
- botón `Seguir` si Amazon lo muestra;
- ninguna obra ajena.

## 8. Qué puede cambiar en el repo después de la sesión

### Caso 1 — Author ID sigue siendo `B0GZFP1JV3`

`NO_CODE_CHANGE`.

### Caso 2 — Amazon cambia/corrige el author ID o URL canónica

Actualizar en el mismo PR, antes de merge:

- `autor.html` → `Person.sameAs`;
- cualquier fuente canónica/generador que posea ese dato;
- tests de identidad/machine authority que lo fijen.

Regenerar artefactos derivados y ejecutar checks.

### Caso 3 — Amazon expone una URL pública estable para una edición que el sitio no identifica correctamente

No añadirla por reflejo. Solo actualizar si representa exactamente la misma edición y mejora la autoridad `sameAs`/identificación sin sustituir el shortlink de compra definido por producto.

## 9. Evidencia que Claude debe devolver a #396

- URL pública final del author page;
- author ID confirmado;
- perfil `CLAIMED/VERIFIED`;
- bio `UPDATED/NO_ACTION`;
- foto `UPDATED/NO_ACTION`;
- Samuel: `ASSOCIATED/ALREADY_ASSOCIATED`;
- Manecillas Kindle: `ASSOCIATED/ALREADY_ASSOCIATED`;
- Manecillas papel: `ASSOCIATED/ALREADY_ASSOCIATED`;
- formato papel↔Kindle: `LINKED` o `ESCALATED`;
- duplicados: `NONE_FOUND` o lista exacta;
- cualquier ticket/owner externo;
- QA público desktop/mobile;
- cambios de repo, si los hubo, + pruebas ejecutadas.

No guardar credenciales, cookies, información fiscal, bancaria ni capturas con datos privados.

## 10. Criterio de cierre

`AUTHOR_PAGE_CLAIMED · PROFILE_COHERENT · SAMUEL_ASSOCIATED · MANECILLAS_KINDLE_ASSOCIATED · MANECILLAS_PAPER_ASSOCIATED · DUPLICATES_REVIEWED · FORMAT_LINKING_VERIFIED_OR_ESCALATED · PUBLIC_DESKTOP_MOBILE_QA_DONE`
