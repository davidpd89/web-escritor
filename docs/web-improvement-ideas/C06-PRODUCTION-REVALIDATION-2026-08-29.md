# C.6 · Revalidación de producción — colaboraciones entre autores

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #181  
Estado: **REJECT_LINK_SWAP · AUTHENTIC_COLLAB_INFRA_STAGED · DRAFT_FIXTURE_ONLY · PUBLICATION_TRIGGER_NOT_MET · NO_CODE**

## Veredicto

Se mantiene el rechazo de cualquier programa de reseñas/backlinks recíprocos pactados como táctica SEO.

La alternativa legítima —colaboraciones editoriales auténticas— ya tiene infraestructura parcial, un fixture de datos y un contrato editorial bien definido, pero no debe activarse hasta contar con participantes reales y el umbral editorial previsto.

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

La ruta pública `/autores/` no existe en la base inspeccionada.

### Dataset existente, pero solo como fixture

`data/autores-red.json` sí existe. Contiene exactamente un autor con:

- `status: "draft"`;
- slug `autor-ejemplo-no-publicar`;
- nombre `AUTOR DE EJEMPLO — NO PUBLICAR`;
- descripción que ordena sustituirlo por una persona real autorizada;
- URLs `example.com`;
- cuatro respuestas de ejemplo que dicen que no deben publicarse.

Por tanto, no existe ningún perfil real aprobado. El builder hace correctamente que ese registro no se publique.

### Inconsistencia dormant de ruta de datos

El docstring de `scripts/build-autores-red.py` muestra como ejemplo `--data content/autores-red.json`, mientras el fixture real actual está en `data/autores-red.json`.

No se corrige ahora porque la feature no está activada y no existe un consumidor/publicación real. Antes de activarla debe normalizarse una única ruta de datos y actualizar script/docs/tests de forma conjunta.

Esto es deuda de activación, no motivo para publicar C.6.

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
AND canonical data path normalized
AND launch/maintenance plan
```

El hecho de que existan script y fixture no es motivo suficiente para generar una colección pública.

## Qué NO implementar

- programa «review por review»;
- tabla de intercambio de enlaces;
- automatización de outreach masivo;
- anchors pactados;
- perfiles sintéticos para llenar `/autores/`;
- scraping de bios;
- publicar el fixture `AUTOR DE EJEMPLO — NO PUBLICAR`;
- publicación de un único invitado para activar la ruta;
- nueva landing de prensa paralela.

## DoD

- [x] política Google vigente revalidada;
- [x] press kit inspeccionado directamente;
- [x] `/autores/` comprobado directamente como no publicado;
- [x] `data/autores-red.json` inspeccionado directamente;
- [x] fixture confirmado como draft/no-publicar;
- [x] builder existente inspeccionado directamente;
- [x] inconsistencia `content/` vs `data/` documentada para activación;
- [x] owner de Drive revisado;
- [x] trigger editorial separado de infraestructura;
- [x] no se crea contenido ficticio;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**REJECT_LINK_SWAP · AUTHENTIC_COLLAB_INFRA_STAGED · DRAFT_FIXTURE_ONLY · PUBLICATION_TRIGGER_NOT_MET · NO_CODE**
