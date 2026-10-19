# Revisión de concursos — 19 de octubre de 2026

Se cotejaron 162 filas de la recopilación de concursos con el radar público.
El inventario de cobertura contiene exclusivamente títulos públicos e identificadores:
[contest-coverage-2026-10-19.json](contest-coverage-2026-10-19.json).
No contiene relatos presentados, plicas, datos personales, prioridades ni notas privadas.

Las 162 filas corresponden a 157 fichas: se agrupan las rondas históricas de
Relatos en Cadena, las dos modalidades de Hislibris y las dos de Elcano. Las dos
modalidades deportivas APDV tienen fichas propias porque sus requisitos y premios
son diferentes. Chamberí ya estaba publicado con otro título y no se duplica.

El radar pasa de 100 a 165 oportunidades fechadas y de 9 a 13 fichas en seguimiento.
Son 69 fichas nuevas netas; AAMA pasa de seguimiento a oportunidad con fecha y PDF
oficial. Al reloj de esta revisión se publican 85 activas, 80 cerradas y 13 en
seguimiento. Las cerradas siguen ocultas hasta marcar «Mostrar vencidas» y no
entran en el calendario. Se añaden 23 fuentes de organizadores a la vigilancia y
se corrige la URL de AAMA hacia la página que enlaza las bases.

## Correcciones y límites de la revisión

- **Silos:** se descarta el enlace anotado de Escritores.org, que entrega las bases
  de otro certamen. Se recupera la convocatoria de Fundación Silos en su dominio
  `.net`.
- **Goles que cuentan:** el PDF universitario confirma la ampliación al 19 de
  octubre, 23:59, hora del centro de México.
- **Proyecto Mariposa:** las 00:00 del 31 de diciembre se expresan como último día
  útil el 30 de diciembre, dejando la hora literal explicada en la ficha.
- **Relatos Subversivos:** se recuperan y revisan las bases originales de los
  convocantes y su documento de aceptación, enlazados en Drive público.
- **Gabriel Aresti:** el boletín oficial confirma la 43.ª edición; se descarta la
  numeración errónea de la ficha informativa.
- **Arteaula:** apertura oficial del 15 de enero al 30 de abril de 2027. Permanece
  como próxima apertura y fuera del calendario de convocatorias abiertas.
- **Belgrano 2026, Prix Hemingway 2027, Valdemembra, Aurelio González Ovies y
  Subur Negre:** visibles como «Pendiente de verificar». No se ha recuperado una
  base primaria actual y completa que permita tratarlos como plazos verificados.
  La ficha distingue datos secundarios, referencias de otra edición y lo que falta
  confirmar. Ninguno entra en ICS.
- Los PDF originales alojados en Escritores.org y las reproducciones íntegras de
  bases se identifican en sus notas. El enlace se llama «Consultar convocatoria y
  bases» para no atribuir condición oficial a un directorio o una noticia.

## Comprobación reproducible

`tests/test-radar-drive-coverage.py` comprueba la cobertura completa a la fecha de
revisión, la separación de las fichas pendientes y la llegada del plazo oficial
de AAMA al calendario. Los contratos existentes comprueban privacidad del esquema,
sincronización HTML/JSON/ICS, reloj de Madrid, caducidad y reconstrucción
determinista. La QA de navegador comprueba filtros, exportaciones, estados y diseño
en los tamaños de pantalla definidos por el repositorio.
