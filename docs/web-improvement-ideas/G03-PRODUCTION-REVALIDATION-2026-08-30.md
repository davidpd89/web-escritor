# G.3 · Revalidación de producción — alt text asistido por IA

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · STRUCTURAL_IMAGE_QA_EXISTS · SEMANTIC_ALT_REMAINS_HUMAN · VOLUME_TRIGGER_NOT_MET · NO_AI_TOOLING`

## Estado real

`main` ya dispone de una capa amplia de QA de imágenes y accesibilidad: tests de formatos/derivados, responsive images, cards sociales, Pa11y y browser QA. No se ha localizado una deuda demostrada de volumen que haga necesario crear ahora un generador IA de `alt`.

La ausencia de un generador no es un gap: la calidad semántica del texto alternativo no puede decidirse mirando únicamente el asset.

## Autoridad normativa vigente

La guía W3C WAI de imágenes, actualizada en 2026, mantiene que el texto alternativo depende del **uso, contexto y propósito** de la imagen. Su árbol de decisión distingue, entre otros casos:

- imagen decorativa o redundante → `alt=""` puede ser correcto;
- imagen funcional → comunicar función/destino;
- imagen informativa → expresar la información esencial;
- imagen compleja → puede requerir equivalente textual más amplio en la página.

Esto confirma el guardrail de G.3: un modelo puede sugerir redacción, pero no puede ser la autoridad que decide qué función cumple la imagen en una URL concreta.

## Qué cubre ya el repositorio

La infraestructura actual cubre problemas estructurales y técnicos como formatos, dimensiones/responsividad, assets y accesibilidad automatizable. Pa11y/browser QA aportan otra barrera contra errores mecánicos.

Lo que esos checks —y tampoco una IA— no pueden resolver de forma fiable es si un `alt` existente es editorialmente el equivalente correcto en contexto.

## Trigger para un piloto

Solo tendría sentido probar tooling IA si aparece un lote real suficientemente grande y la redacción inicial consume tiempo material. Antes de generar, cada imagen debe clasificarse como:

- `DECORATIVE`;
- `FUNCTIONAL`;
- `INFORMATIVE`;
- `COMPLEX`.

Después, una persona debe revisar el asset junto a la página, texto vecino, caption, destino del enlace y canon.

## Guardrails

- No autocorrección/autocommit en CI.
- No rellenar `alt=""` decorativos para conseguir una falsa sensación de cobertura.
- No OCR automático de portadas como `alt` por defecto.
- No inferir emociones, identidades, relaciones o atributos sensibles.
- No usar `alt` como campo SEO.
- No subir assets privados/no publicados a proveedores externos sin rights/privacy review.
- No publicar outputs sin revisión humana contextual.

## Decisión productiva

No se añade código ni proveedor. El owner sigue siendo el proceso editorial humano apoyado por los checkers estructurales existentes. Si un futuro lote demuestra ahorro real, G.3 permite un piloto privado de sugerencias; no un generador autónomo.

## Cierre

`CONDITIONAL` no significa «tool pendiente». Significa que el recurso puede ser útil únicamente ante volumen demostrado y siempre subordinado a la decisión contextual humana.