# C.8 · Revalidación de producción — «Empieza aquí» por rutas de lector

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #183  
Estado: **ALREADY_IMPLEMENTED · ROUTES_CLEAR · MEASUREMENT_PARTIAL · HOLD_EXPANSION · NO_UI_CHANGE**

## Veredicto

La superficie `/empieza-aqui/` ya cumple la función principal de C.8. No debe sustituirse por otra landing, quiz o selector de pseudo-personas.

La revalidación detecta un único hueco real: la elección de ruta no se mide de manera uniforme. Ese hueco no justifica rediseñar la página ni introducir otro sistema de analytics.

## Evidencia directa de `main`

`empieza-aqui/index.html` es una URL canónica e indexable con H1 «¿Por dónde empiezas?» y siete rutas explícitas:

1. obra actual / Las manecillas del recuerdo;
2. Samuel entre mundos / Noveris;
3. autor;
4. lectura;
5. escritura y publicación;
6. prensa y eventos;
7. mapa completo del sitio.

La estructura usa necesidades reales y destinos concretos. No depende de perfiles inventados como «lector soñador» o «escritor avanzado».

## Arquitectura

La página ya enlaza a los owners correctos en vez de duplicar su contenido:

- Manecillas → ficha/fragmentos;
- Samuel/Noveris → libro/universo;
- autor → `/autor.html`;
- lectura → Cuaderno/Recomendaciones;
- escritura → Herramientas/Editoriales;
- prensa → `/prensa.html` y `/eventos.html`;
- exploración total → `/mapa-del-sitio/`.

No hace falta otro hub de findability.

## Analytics real

`data/analytics-events.json` es la autoridad única de nombres de evento y el runtime global usa GoatCounter.

La taxonomía actual ya contiene, entre otros:

- `leer-fragmento-samuel`;
- `leer-fragmento-manecillas`;
- `explorar-noveris`;
- `ver-prensa`;
- `download-press-kit`.

Por tanto algunos clics desde `/empieza-aqui/` quedan medidos de forma indirecta por su destino.

Pero no existe un evento canónico que responda de forma uniforme a:

> «¿qué ruta de Empieza aquí eligió el usuario?»

Las rutas de autor, lectura, escritura/publicación y mapa del sitio no quedan representadas como una misma familia comparable de decisiones.

Estado correcto: `MEASUREMENT_PARTIAL`.

## Por qué no se implementa tracking ad hoc en esta PR

C.8 no debe crear:

- un segundo proveedor;
- un script de analytics paralelo;
- eventos fuera de `data/analytics-events.json`;
- un inline tracker aislado solo para esta página;
- duplicación de eventos que ya cuentan navegación editorial.

El owner correcto es la taxonomía/runtime global de analytics. Cuando ese owner se amplíe, la instrumentación de C.8 debe entrar allí de manera coherente y cubierta por `scripts/check-analytics-taxonomy.py`.

## Contrato recomendado para una futura instrumentación

Una única familia semántica, por ejemplo:

```text
start_here_route_click
context = manecillas | samuel_noveris | autor | lectura | escritura | prensa_eventos | mapa_sitio
```

La nomenclatura final debe adaptarse a la convención aprobada por el owner de analytics; este documento no introduce un literal de runtime por su cuenta.

Debe medir solo la elección explícita de ruta, sin PII, fingerprinting ni nuevos proveedores.

## Qué medir antes de expandir UX

- distribución de clics por ruta;
- rutas con uso casi nulo;
- rutas que concentran la mayoría de salidas;
- si los usuarios regresan inmediatamente a navegación global;
- si aparecen destinos frecuentes no representados.

Solo después puede evaluarse reordenar, simplificar o añadir una ruta.

## Qué NO hacer

- segunda página «para nuevos lectores»;
- quiz obligatorio;
- modal previo a navegar;
- personalización basada en datos sensibles;
- perfiles ficticios;
- duplicar `/mapa-del-sitio/`;
- crear una nueva taxonomía de analytics solo para C.8;
- cambiar copy/orden sin evidencia.

## Gate de expansión

```text
measured route behavior
AND repeated findability problem
AND clear hypothesis
AND change can be tested without duplicating navigation
```

Mientras no se cumpla: mantener la página actual.

## DoD

- [x] página real inspeccionada directamente;
- [x] siete rutas reales identificadas;
- [x] owners de destino verificados;
- [x] taxonomía analytics inspeccionada directamente;
- [x] medición parcial diferenciada de medición uniforme;
- [x] no se crea landing/quiz paralelo;
- [x] contrato futuro asignado al owner global de analytics;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**ALREADY_IMPLEMENTED · ROUTES_CLEAR · MEASUREMENT_PARTIAL · HOLD_EXPANSION · NO_UI_CHANGE**
