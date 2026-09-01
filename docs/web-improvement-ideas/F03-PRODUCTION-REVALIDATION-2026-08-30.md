# F.3 · Revalidación de producción — captions, transcripciones y media temporal

**Fecha inicial:** 2026-08-30  
**Corrección de evidencia:** 2026-08-31  
**Verificación de audio:** 2026-09-01  
**Base inspeccionada:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · HOME_TEMPORAL_MEDIA_EXISTS · MUTED_INLINE_INTRO · NO_AUDIO_TRACK_VERIFIED_DECORATIVE · VISUAL_ESSENTIALITY_NOT_VERIFIED · MEDIA_OBLIGATION_PRESERVED · NO_CODE`

## 1. Conclusión

La obligación de accesibilidad se mantiene, pero no existe evidencia suficiente para ordenar una campaña global de captions/transcripciones.

La revalidación del 30/08 contenía una premisa factual incorrecta: afirmaba que el `main` inspeccionado no contenía media temporal pública. El 31/08 se ha comprobado directamente que HOME sí incluye una intro `<video>` y que los assets MP4/WebM existen.

La presencia del vídeo activa **clasificación**, no una conclusión automática de `TRANSCRIPT_REQUIRED`. Antes de decidir la alternativa WCAG correcta hay que inspeccionar el contenido temporal real y sus tracks.

## 2. Inventario directo corregido

`index.html` en el `main` exacto contiene:

```html
<video class="intro__video" muted playsinline preload="auto" poster="assets/hero-tinta-poster.jpg?v=2" data-hero-video>
  <source src="assets/video/hero-tinta-david-porto.webm?v=2" type="video/webm" />
  <source src="assets/video/hero-tinta-david-porto.mp4?v=2" type="video/mp4" />
</video>
```

El directorio `assets/video/` contiene:

- `hero-tinta-david-porto.mp4` (~630 KB);
- `hero-tinta-david-porto.webm` (~602 KB).

También existe poster estático y el runtime `assets/v1-shell.js` gobierna reproducción/salida. El elemento se declara `muted` + `playsinline`, y `<noscript>` oculta la intro para dejar accesible la HOME normal sin JavaScript.

#163 no introdujo esta media: su patch de `index.html` respecto a `main` solo actualiza el query de `v1-home.css`. Por tanto la intro pertenece al baseline que esta PR debía inventariar.

No se ha demostrado en cambio una superficie pública adicional de audio/vídeo temporal relevante mediante YouTube/Vimeo u otros players.

## 3. Qué queda por verificar antes de remediar

La estructura del repo no certifica por sí sola:

- si MP4/WebM contienen una pista de audio aunque la reproducción HTML sea `muted`;
- si existe habla o sonido informativo;
- si la animación contiene información visual esencial que no aparezca en otro lugar;
- si la pieza es puramente decorativa/de identidad y no transmite contenido necesario.

Estado corregido el 01/09: los dos primeros puntos (pista de audio, habla o sonido informativo) quedan `NO_AUDIO_TRACK_VERIFIED_DECORATIVE` — ver sección 7-bis. Los dos últimos (esencialidad de la información visual) siguen `VISUAL_ESSENTIALITY_NOT_VERIFIED`.

No se etiqueta el vídeo como `captioned`, `transcript_required` ni `verified_accessible` hasta inspeccionar también la esencialidad visual real. Sí queda descartado `transcript_required` por audio, porque no existe pista de audio que transcribir.

## 4. Contrato normativo que debe conservarse

La obligación se evalúa por el contenido real, no mediante la regla falsa «todo vídeo necesita transcript»:

- audio-only pregrabado: alternativa temporal equivalente cuando aplique WCAG 1.2.1;
- vídeo-only pregrabado: alternativa o audio equivalente según 1.2.1;
- audio pregrabado dentro de media sincronizada: captions según 1.2.2;
- media sincronizada pregrabada: alternativa/audio description en 1.2.3 y audio description en AA según 1.2.5 cuando información visual necesaria no esté ya disponible en audio;
- media en directo: captions AA según 1.2.4 cuando proceda.

La implementación debe verificar el estándar vigente y el contenido concreto antes de decidir el formato de alternativa.

## 5. Trigger y secuencia de cierre

Para HOME:

1. inspeccionar MP4/WebM con `ffprobe` o equivalente y revisar visualmente la secuencia;
2. documentar si existe audio track y si contiene información;
3. documentar si la información visual es esencial o decorativa/redundante con la HOME;
4. solo si surge una obligación concreta, corregir la superficie propietaria y añadir QA específico;
5. coordinar con #163, que mantiene aparte una incidencia real de reproducción Safari/iPhone. Compatibilidad de autoplay y accesibilidad de contenido son problemas distintos.

Para futuras superficies: reabrir F.3 cuando aparezca audio/vídeo temporal real con habla, sonido informativo o información visual necesaria y no exista alternativa equivalente.

## 6. Guardrails

- No crear transcripts vacíos o de contenido inexistente.
- No confundir vídeo decorativo/silencioso con vídeo informativo.
- No asumir que `muted` significa que el fichero no contiene pista de audio (verificado empíricamente el 01/09, ver sección 7-bis; para esta pareja concreta de ficheros la asunción resultó cierta, pero se comprobó, no se dio por hecho).
- No asumir que subtítulos automáticos externos son suficientes sin revisar precisión y disponibilidad.
- No duplicar texto si el medio está claramente presentado como alternativa de un contenido textual equivalente.
- No declarar cumplimiento por la mera existencia de un `<track>`; la alternativa debe corresponder al contenido real.
- No convertir la incidencia iOS de #163 en argumento para captions/transcripción: primero clasificar contenido, después compatibilidad.

## 7. Estado final de F.3

`CONDITIONAL · HOME_TEMPORAL_MEDIA_EXISTS · MUTED_INLINE_INTRO · NO_AUDIO_TRACK_VERIFIED_DECORATIVE · VISUAL_ESSENTIALITY_NOT_VERIFIED · MEDIA_OBLIGATION_PRESERVED · NO_CODE`

La idea sigue siendo una obligación condicional. La deuda inmediata es de **clasificación correcta de la media existente**, no una infraestructura global de transcripciones.

## 7-bis. Verificación directa de pista de audio (2026-09-01)

Se ejecutó `ffprobe` (8.1.2) directamente sobre los dos ficheros publicados en `assets/video/` del `main` inspeccionado, sin ninguna llamada de red:

```
$ ffprobe -v error -show_entries stream=index,codec_name,codec_type -of default=noprint_wrappers=1 assets/video/hero-tinta-david-porto.mp4
index=0
codec_name=h264
codec_type=video

$ ffprobe -v error -show_entries stream=index,codec_name,codec_type -of default=noprint_wrappers=1 assets/video/hero-tinta-david-porto.webm
index=0
codec_name=vp9
codec_type=video

$ ffprobe -v error -show_format assets/video/hero-tinta-david-porto.mp4
duration=5.000000
size=630059
nb_streams=1
```

Ambos contenedores declaran `nb_streams=1` y ese único stream es de vídeo (`h264`/`avc1` en el MP4, `vp9` en el WebM; 720×1280, 24 fps, 5.00 s). Ninguno de los dos ficheros tiene una segunda pista, de audio o de otro tipo. No es una pista de audio silenciosa — es la ausencia total de pista de audio a nivel de contenedor, verificable sin reproducir ni "escuchar" el fichero.

Consecuencia directa para la sección 3: no puede haber habla ni sonido informativo en un fichero sin pista de audio. Los puntos 1 y 2 de la sección 3 quedan cerrados como `NO_AUDIO_TRACK_VERIFIED_DECORATIVE`. WCAG 1.2.2 (captions) y 1.2.1/1.2.3 en su vertiente de audio no aplican porque no existe audio pregrabado que subtitular o transcribir.

Esto **no** cierra F.3 por completo: los puntos 3 y 4 de la sección 3 (si la animación visual de 5 s transmite información esencial no disponible en otro lugar de la HOME, relevante para la vertiente vídeo-only de 1.2.1) siguen sin inspeccionarse visualmente y quedan `VISUAL_ESSENTIALITY_NOT_VERIFIED`. Dado el nombre del asset (`hero-tinta-david-porto`, animación de tinta de marca/identidad en el hero) y su brevedad (5 s, loop de intro), la hipótesis de trabajo es contenido decorativo/de marca redundante con el H1 y la identidad visual ya presentes en la HOME — pero esa hipótesis no se marca como verificada aquí porque requiere inspección visual humana, no solo de contenedor.