# C.6 · Revalidación de producción — colaboraciones entre autores

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #181  
Estado: **REJECT_LINK_SWAP · AUTHENTIC_COLLAB_INFRA_STAGED · PUBLICATION_TRIGGER_NOT_MET · NO_CODE**

## Veredicto

Se mantiene el rechazo de cualquier programa de reseñas/backlinks recíprocos pactados como táctica SEO.

La alternativa legítima —colaboraciones editoriales auténticas— ya tiene infraestructura parcial y un contrato editorial bien definido, pero no debe activarse hasta contar con participantes reales y el umbral editorial previsto.

## Evidencia directa de `main`

### Press kit ya existe

`/prensa.html` ya es la superficie pública para entrevistas, reseñas, presentaciones y materiales de medios. Incluye:

- bios listas para uso;
- foto editorial y fotos de eventos;
- fichas técnicas de Manecillas y Samuel;
- sinopsis y materiales;
- contacto para medios.

C.6 no necesita otra landing de outreach.

### Infraestructura `Autores en primera persona`

`main` contiene `scripts/build-autores-red.py`.

El builder:

- genera `/autores/` y perfiles estáticos desde datos revisados;
- no publica registros `draft`;
- exige respuestas originales;
- valida URLs HTTPS;
- no obtiene contenido de terceros;
- usa `ProfilePage`/`Person` y `CollectionPage`/`ItemList`;
- integra el shell común.

Sin embargo, en la base inspeccionada:

- `/autores/` no existe;
- `content/autores-red.json` no existe.

Por tanto, la infraestructura está **staged**, no publicada.

## Owner editorial de Drive

`README_AUTORES_RED.md` define el MVP y su gate:

- permiso del autor;
- descripción revisada;
- mínimo cuatro respuestas originales;
- URLs oficiales HTTPS;
- revisión manual;
- no backlink obligatorio;
- no venta de dofollow;
- no bios copiadas;
- no publicación vacía o con un solo invitado.

Umbral previsto: 5–8 perfiles reales, diversidad de géneros y preguntas originales.

Ese documento ya resuelve la parte legítima de C.6. No hace falta otro programa ni CRM SEO.

## Política de enlaces vigente

Google sigue considerando *link spam*:

- comprar/vender enlaces para ranking;
- intercambiar bienes/servicios por enlaces;
- intercambios excesivos del tipo «link to me and I'll link to you»;
- exigir enlaces contractualmente sin permitir cualificación;
- guest posts/advertorials con anchors optimizados que transmiten ranking credit.

Por tanto C.6 mantiene una frontera simple:

```text
authentic editorial collaboration = allowed
mandatory reciprocal review/link/anchor = reject
```

## R.19 — earned media

La vía correcta es responder a oportunidades periodísticas cuando exista experiencia real y una aportación útil. El backlink puede ocurrir, pero no es condición ni objeto de negociación.

El press kit actual ya reduce fricción para esa vía.

## R.20 — link reclamation

Sigue siendo válida solo para corregir un enlace o mención ya existente:

- URL rota/404;
- URL canónica antigua;
- dato bibliográfico incorrecto;
- host/protocolo obsoleto;
- mención sin enlace cuando la referencia oficial es inequívoca y la corrección aporta utilidad.

No pedir anchor optimizado ni contraprestación.

## Trigger para publicar `/autores/`

No activar el builder hasta cumplir:

```text
>= 5 real approved profiles
AND explicit participation permission
AND original first-person answers
AND editorial review owner
AND no backlink obligation
AND launch/maintenance plan
```

El hecho de que exista el script no es motivo suficiente para generar una colección vacía.

## Qué NO implementar

- programa «review por review»;
- tabla de intercambio de enlaces;
- automatización de outreach masivo;
- anchors pactados;
- perfiles sintéticos para llenar `/autores/`;
- scraping de bios;
- publicación de un único invitado para activar la ruta;
- nueva landing de prensa paralela.

## DoD

- [x] política Google vigente revalidada;
- [x] press kit inspeccionado directamente;
- [x] `/autores/` comprobado directamente como no publicado;
- [x] `content/autores-red.json` comprobado directamente como ausente;
- [x] builder existente inspeccionado directamente;
- [x] owner de Drive revisado;
- [x] trigger editorial separado de infraestructura;
- [x] no se crea contenido ficticio;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**REJECT_LINK_SWAP · AUTHENTIC_COLLAB_INFRA_STAGED · PUBLICATION_TRIGGER_NOT_MET · NO_CODE**
