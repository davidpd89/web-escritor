# Verificación de mención externa hoymadrid.app

Fecha: 2026-08-22

Objetivo: recuperar la mención externa de la presentación de Samuel entre mundos solo si la URL seguía activa.

## Comprobaciones ejecutadas

1. Candidatas por slug histórico:
- https://hoymadrid.app/planes/presentacion-de-samuel-entre-dos-mundos
- https://hoymadrid.app/planes/presentacion-de-samuel-entre-mundos

Resultado con `Invoke-WebRequest` (GET):
- ambas devuelven HTTP 404.

2. Descubrimiento por sitemap:
- https://hoymadrid.app/sitemap.xml

Resultado:
- respuestas HTTP 308/HTTP 000 en cliente local y sin URL resoluble con mención de Samuel.

## Decisión

No se restaura ningún enlace a hoymadrid.app en `eventos.html` ni `prensa.html` para evitar publicar evidencia rota.

La tarea se considera cerrada por verificación negativa documentada. Si el dominio vuelve a publicar una URL estable y verificable, se añadirá junto al evento que acredita, con `rel="noopener noreferrer"`.
