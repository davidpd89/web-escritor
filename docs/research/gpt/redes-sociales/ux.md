# #704 · Contrato público y composición segura de estadísticas sociales

**22/10/2026 · PR hija de #699.** El cambio es un **compositor de datos ejecutable y probado**, NO una página desplegada. Ningún cambio a `autor.html`, navegación, Actions o `main`.

## Problema concreto

Los lectores de #705 (Metricool/Threads), #706 (Bluesky) y #707 (Mastodon) producen **objetos distintos**: Metricool identifica `observed_at` con `YYYY-MM-DD` de un día cerrado y las APIs públicas incluyen hora UTC. Si sumamos sus seguidores sin validar fechas, identidad y nulos, el dashboard puede mostrar cifras antiguas, duplicadas, de otro perfil o un «total» presentado como personas únicas.

**Solución implementada:** [scripts/research/gpt_social_compose.py](../../../../scripts/research/gpt_social_compose.py) recibe esos objetos **sin alterar los lectores** y emite un único contrato público limitado a las métricas demostradas. [26 pruebas offline](../../../../tests/test_gpt_social_compose.py) ejecutadas y verificadas contra hashes de GitHub (detalles abajo).

Las URL oficiales de **solo estas tres** redes proceden de `autor.html` y `scripts/build-site-shell.py` (revisados en el repositorio vigente). No introducir URLs devueltas por APIs sin comparar antes con esas fuentes.

## Comportamiento del código

1. Reconoce exclusivamente `bluesky`, `mastodon` y `threads`. Rechaza IDs desconocidos, repetidos o enlaces diferentes de los oficiales. Faltantes figuran como `pending`; no se transforman en cero.
2. Acepta seguidores solo si son un entero no negativo (**`True` no es `1`**). `views_30d`, `impressions_30d` e `interactions_30d` deben ser `null` o estar ausentes: ninguna vista ambigua puede sumarse.
3. Normaliza ISO con zona horaria para Bluesky/Mastodon y fechas de cierre de día `YYYY-MM-DD` para Metricool con `zoneinfo.ZoneInfo("Europe/Madrid")`. Rechaza días inacabados y marcas temporales futuras.
4. Política **provisional y explícita de frescura: 48 horas** desde la observación. Un seguidor de fecha caducada se convierte en `null` con estado `stale` y **sale del total**. El resumen informa de cobertura, p. ej., «2 de 3 redes con datos vigentes». Ese plazo es una decisión editorial propia, NO una obligación de ninguna API.
5. El sumatorio se denomina **«Seguidores sumados en redes con datos vigentes (no personas únicas)»**. No presupone que la misma persona no siga dos redes; `coverage/eligible` cuentan las **tres redes admitidas**, no todas las redes sociales del autor.
6. No copia del origen `DID`, ID local, token ni datos auxiliares. El formato público contiene exclusivamente `id`, `profile_url` canónica, `followers`, `observed_at`, `source`, `status`, fecha de generación y sumatorio/cobertura.
7. Salida por defecto a **stdout**. Si se indica `--output`, escribe temporal en el mismo directorio y reemplaza con `os.replace`; errores de formato no sobrescriben el archivo anterior. Bloquea `--output` sin fuentes y destino igual a un archivo de entrada. **No** se añadió un workflow ni escritura automática al directorio público.

### Ejecución reproducible (sin servicios externos)

~~~bash
python -m unittest discover -s tests -p 'test_gpt_social_compose.py' -v
python scripts/research/gpt_social_compose.py  # JSON válido, 3 cuentas pending, ningún cero inventado

# Solo después de obtener y validar snapshots privados de #705-#707:
python scripts/research/gpt_social_compose.py \
  /ruta/privada/bluesky.json /ruta/privada/mastodon.json /ruta/privada/threads.json \
  --output /tmp/social-metrics.json
~~~

Salida estructural sin cifras inventadas:

~~~json
{
  "schema_version": 1,
  "generated_at": "2026-10-22T12:00:00Z",
  "networks": [
    {"id":"bluesky","profile_url":"https://bsky.app/profile/davidportoescritor.bsky.social","followers":null,"observed_at":null,"source":null,"status":"pending"},
    {"id":"mastodon","profile_url":"https://mastodon.social/@davidportodiaz","followers":null,"observed_at":null,"source":null,"status":"pending"},
    {"id":"threads","profile_url":"https://www.threads.com/@davidportodiaz","followers":null,"observed_at":null,"source":null,"status":"pending"}
  ],
  "totals": {"follower_relationships":null,"coverage":0,"eligible":3,"label":"Seguidores sumados en redes con datos vigentes (no personas únicas)"}
}
~~~

La fecha del ejemplo representa una ejecución de prueba, no un dato extraído de una API. La futura ruta `data/social-metrics.generated.json` se mantiene **sin crear**; el programa permite probar en `/tmp` antes de autorizar la publicación.

## 6 pruebas cruzadas nuevas sin fusionar PR

[tests/test_gpt_social_pipeline.py](../../../../tests/test_gpt_social_pipeline.py) importa **los propios normalizadores de las tres PR hermanas**, construye respuestas sintéticas, compone sus salidas, escribe un fichero real en un directorio temporal y valida cifras y privacidad. Si esas ramas no están presentes, los **6 tests quedan `skipped`**: la PR #704 aislada no afirma tener los módulos de las otras hijas.

Reproducción exacta de la prueba cruzada en un directorio local temporal desde un checkout del repositorio. Solo lectura: **NO merge, NO Actions, NO commits y NO métricas reales**:

~~~bash
git fetch origin \
  +refs/heads/research/gpt-social-ux-2026-10-22:refs/remotes/origin/research/gpt-social-ux-2026-10-22 \
  +refs/heads/research/gpt-social-metricool-2026-10-22:refs/remotes/origin/research/gpt-social-metricool-2026-10-22 \
  +refs/heads/research/gpt-social-bluesky-2026-10-22:refs/remotes/origin/research/gpt-social-bluesky-2026-10-22 \
  +refs/heads/research/gpt-social-mastodon-2026-10-22:refs/remotes/origin/research/gpt-social-mastodon-2026-10-22

tmp="$(mktemp -d)"
mkdir -p "$tmp/scripts/research" "$tmp/tests"
copy_from() {
  git show "origin/$1:$2" > "$tmp/$2"
}
copy_from research/gpt-social-ux-2026-10-22 scripts/research/gpt_social_compose.py
copy_from research/gpt-social-ux-2026-10-22 tests/test_gpt_social_compose.py
copy_from research/gpt-social-ux-2026-10-22 tests/test_gpt_social_pipeline.py
copy_from research/gpt-social-metricool-2026-10-22 scripts/research/gpt_metricool_threads.py
copy_from research/gpt-social-metricool-2026-10-22 tests/test_gpt_metricool_threads.py
copy_from research/gpt-social-bluesky-2026-10-22 scripts/research/gpt_social_bluesky.py
copy_from research/gpt-social-bluesky-2026-10-22 tests/test_gpt_social_bluesky.py
copy_from research/gpt-social-mastodon-2026-10-22 scripts/research/gpt_social_mastodon.py
copy_from research/gpt-social-mastodon-2026-10-22 tests/test_gpt_social_mastodon.py

python -m unittest discover -s "$tmp/tests" -p 'test_gpt_*.py' -v
~~~

**Resultado en entorno local de investigación:** 74 pruebas unitarias de las PR individuales + **6 pruebas cruzadas** = **80 PASS**, Python 3.13, sin red ni GitHub Actions. Los **4 scripts bajo test** coincidían byte a byte con el Git blob de su PR (hashes de adaptadores: #704 `20c9650b`, #705 `cccaa4cf`, #706 `1f4de0ab`, #707 `79345fd8`). Las pruebas cruzadas no son lecturas live de APIs: repetir el comando anterior tras unir temporalmente las versiones definitivas.

**Casos de integración:** las tres salidas producen suma y cobertura correctas; archivos fuente → CLI → JSON público; salida sin DID ni ID local; los seguidores caducados no inflan totales; vistas no verificadas se rechazan; identidades falsas se rechazan antes de componer.

**Pendiente:** comprobar Bluesky/Mastodon contra las API reales, integración del frontend, accesibilidad y transporte automatizado de Metricool. Las 80 pruebas offline NO equivalen a despliegue funcional.

## Verificación realizada

`python -m unittest discover -s tests -p test_gpt_social_compose.py -v` → **26/26 PASS** en Python 3.13, fuera de GitHub Actions. Se cotejaron los hashes Git exactos de script y test locales contra los blobs de la PR.

Las pruebas abarcan: formatos concretos de #705/#706, inclusión de #707; sumatorios y cobertura; `null` frente a 0; duplicados y URLs impostoras; métricas no verificadas; campos extra no expuestos; 48 h exactas y caducidad; zonas de hora de Madrid en 21 y 25/10/2026 (cambio a horario de invierno); fechas futuras y sin zona; escritura atómica; no sobrescribir cuando no hay fuentes ni cuando el destino coincide con un origen.

**No probado:** conexión real entre ramas hijas, página pública, validación con la suite del repo, compatibilidad Windows sin base IANA de zonas ni publicación automatizada. En Windows `zoneinfo` podría requerir [tzdata](https://docs.python.org/3/library/zoneinfo.html); comprobarlo antes de integración multiplataforma.

## Diseño concreto del futuro bloque de la página (#704, NO implementado todavía)

- Encabezado editorial sugerido: **«Donde seguimos hablando de libros»**. Subtexto: «Lecturas, escritura y cultura, también en mis redes».
- Tres tarjetas por ahora, **Bluesky, Mastodon, Threads**, con enlaces canónicos ya presentes en la web y CTA **«Ver perfil en Bluesky/Mastodon/Threads»**. No simular una acción «Seguir» que requiera autorización del visitante.
- Mostrar seguidores solo si `status=ok`; si `stale` o `pending`, mostrar **«Dato no disponible»** o **«Última cifra sin actualizar»** con fecha si existe.
- Encima de las tarjetas, mostrar suma **solo con `coverage > 0`** y la cobertura visible (**«X de 3 redes con datos vigentes»**). Nunca presentar la cifra como comunidad única ni extender «3» a las demás cuentas activas.
- Sin JS, enlaces y contenido principal deben seguir accesibles; no usar iframes ni terceros para obtener métricas desde el navegador. Los SVG pueden extraerse de iconos **ya existentes** en el shell; consultar antes de importar librerías adicionales.

## Fuentes y por qué se eligió esta implementación

- **Código comprobado del repositorio:** `scripts/build-human-site-stats.py` ya genera JSON local en la arquitectura GitHub Pages estática. Se reutiliza **el patrón de separar generador y dato publicado**, no sus métricas de libros.
- [JSON Schema, especificación y pruebas oficiales](https://json-schema.org/understanding-json-schema/reference/object): los objetos permiten propiedades adicionales si no se prohíben explícitamente. El compositor aplica **lista permitida de campos de salida**, sin vendoring de validadores ni dependencias; la [suite oficial](https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft2020-12/additionalProperties.json) demuestra el comportamiento que se evita. No se ha copiado código de terceros a esta PR.
- [Python `zoneinfo`](https://docs.python.org/3/library/zoneinfo.html) calcula el huso de Madrid con DST; [`os.replace`](https://docs.python.org/3.13/library/os.html#os.replace) permite sustitución atómica en el mismo filesystem.

**Puerta de integración para Claude:** confirmar identidad real y lectores de #705–#707; resolver qué hacer cuando una red no entregue snapshot nuevo (caché/edad del JSON en frontend); decidir TTL definitivo; ejecutar la suite completa y crear la UI/navigation/sitemap solo en PR aparte cuando esté aprobado. **No confundir 26 pruebas offline con una prueba de despliegue.**
