# F.3 · Revalidación de producción — captions, transcripciones y media temporal

**Fecha:** 2026-08-30  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · MEDIA_OBLIGATION_PRESERVED · TRIGGER_NOT_MET · NO_CODE`

## 1. Conclusión

La obligación de accesibilidad se mantiene, pero no existe hoy un trigger de producto que justifique una campaña global de captions/transcripciones.

En el `main` inspeccionado no se han localizado superficies públicas con audio o vídeo temporal que contengan habla o información y que requieran remediación ahora. Por tanto F.3 no debe crear reproductores, pistas VTT, páginas de transcript ni infraestructura vacía.

## 2. Inventario directo del repositorio

Se comprobó el árbol/código actual buscando:

- ficheros `.mp4`, `.webm`, `.mp3`, `.wav`, `.ogg`, `.m4a`;
- pistas `.vtt`;
- embeds/enlaces de YouTube y Vimeo;
- etiquetas HTML `<video>` y `<audio>`.

El inventario no devuelve media pública temporal en esas formas. La existencia de lógica genérica del Service Worker para no interceptar `Range`/audio/vídeo no demuestra que haya actualmente una superficie editorial pública con media temporal.

## 3. Contrato normativo que sí debe conservarse

Si en el futuro se publica media real, la obligación se evalúa por tipo de contenido, no por una regla genérica de «todo vídeo necesita transcript»:

- audio-only pregrabado: alternativa temporal equivalente cuando aplique WCAG 1.2.1;
- vídeo-only pregrabado: alternativa o audio equivalente según 1.2.1;
- audio pregrabado dentro de media sincronizada: captions según 1.2.2;
- media sincronizada pregrabada: alternativa/audio description en 1.2.3 y audio description en AA según 1.2.5 cuando la información visual necesaria no esté ya en el audio;
- media en directo: captions AA según 1.2.4 cuando proceda.

La implementación futura debe verificar el estándar vigente en ese momento y el contenido concreto antes de decidir el formato de alternativa.

## 4. Trigger de reapertura

Reabrir F.3 cuando aparezca al menos una superficie pública con:

1. audio o vídeo temporal real;
2. habla, sonido informativo o información visual necesaria para comprender/completar la experiencia;
3. ausencia de alternativa accesible equivalente ya publicada.

Entonces se corrige la superficie propietaria y se añade QA específico para que la alternativa no desaparezca en cambios posteriores.

## 5. Guardrails

- No crear transcripts vacíos o de contenido inexistente.
- No confundir vídeo decorativo/silencioso con vídeo informativo.
- No asumir que subtítulos automáticos externos son suficientes sin revisar precisión y disponibilidad real.
- No duplicar texto si el propio medio está claramente presentado como alternativa de un contenido textual equivalente.
- No declarar cumplimiento por la mera existencia de un `<track>`; la alternativa debe corresponder al contenido real.

## 6. Estado final de F.3

`CONDITIONAL · MEDIA_OBLIGATION_PRESERVED · TRIGGER_NOT_MET · NO_CODE`

La idea sigue siendo válida como obligación condicional de accesibilidad. No existe deuda de producción demostrada que justifique código en el corte actual.