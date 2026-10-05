# Post-deploy QA pendiente de dispositivo real

Estas pruebas no deben darse por cubiertas por emulación Playwright. Requieren hardware, navegador o tecnología de asistencia real.

## Matriz pendiente

- iPhone/iPad con Safari estable: navegación por toque, zoom del sistema, orientación, teclado virtual, instalación PWA y vuelta desde enlaces externos.
- Android con Chrome estable: teclado virtual, selectores nativos, atrás/adelante, PWA instalada y modo avión.
- Windows + Edge/Chrome + NVDA: landmarks, orden de lectura, nombres de controles, diálogo Explorar, filtros y mensajes `aria-live`.
- macOS + Safari + VoiceOver: rotor de encabezados/enlaces, diálogo modal y restauración de foco.
- Windows High Contrast nativo: controles, focus ring, badges de estado y enlaces dentro de tarjetas.
- Zoom real de navegador al 200 % y 400 % en escritorio, especialmente Editoriales, Convocatorias, Herramientas y Prensa.
- Impresión/PDF real en A4 y Letter: Home, fichas de libros, Editoriales, Convocatorias y Prensa; sin overlays ni cortes de texto.
- Red lenta/offline real tras una visita previa: service worker, fallback offline, ausencia de datos dinámicos obsoletos y recuperación al volver online.
- Navegación solo con teclado físico en Safari/Firefox/Edge: ningún focus trap fuera de diálogos y foco siempre visible.
- Compartir URLs con filtros/hash y abrirlas en otro dispositivo: mismo estado sin crear canonicals alternativos.

## Evidencia mínima

Registrar fecha, dispositivo/SO/navegador, ruta, resultado, captura o vídeo si falla y pasos exactos de reproducción. Un fallo reproducible debe convertirse después en test automatizado cuando sea técnicamente posible.
