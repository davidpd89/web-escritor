# Pendientes y decisiones del catálogo de lecturas (22/10/2026)

## Pendiente a futuro
- **Microsoft Clarity** (proyecto `wxkseslr28`): revisar grabaciones y mapas de calor para detectar problemas de uso en menús y catálogo. Requiere iniciar sesión en Clarity o un token de su API; no se usan las sesiones de Edge abiertas porque son de redes sociales.
- **Planeta de Libros como segunda fuente de novedades**: la investigación está hecha (página Next.js, ISBN en la tabla de ficha técnica, `fechaPublicacion` en el JSON embebido). Decisión del propietario: las portadas se pueden reutilizar sin restricción. Falta implementar el lector (`penguin_edition` tiene un equivalente a seguir).
- **Creators API de Amazon**: bloqueada hasta alcanzar el umbral de ventas cualificadas. El sistema se construye sin ella (PVP editorial desde la ficha de Penguin). Si algún día se consigue, se activa el adaptador existente.

## Hecho en esta fase
- Calendario de próximos lanzamientos: `/recomendaciones/proximos-lanzamientos.ics`, generado por el constructor del catálogo con fechas de publicación completas posteriores a los datos; enlazado como «Añadir al calendario» desde la ficha de cada libro que aún no ha salido.
- Monitor semanal de fuentes del radar de concursos (`scripts/radar_source_monitor.py`, workflow `radar-source-monitor.yml`): mantiene un único aviso en GitHub con lo que hay que revisar y no publica nada solo.
- Enlaces externos de concursos que fallan por caídas de sus webs (000/500/503) excluidos de la comprobación en `.lycheeignore`.
