# 15 — Anti-slop design review (gate operativo)

**Por qué existe:** la kill-list de `README.md` ("Kill-list resumida") enumera 25 patrones a rechazar por defecto, pero una lista de nombres no es un gate — no dice cuándo un elemento de la lista es realmente el problema, ni cuándo una excepción está justificada. Este fichero convierte esa lista en `DUX-117 · Anti-slop review obligatorio` (`13-BACKLOG-IMPLEMENTACION-CLAUDE.md`): un paso de revisión con criterio de aceptación/rechazo concreto, aplicable a **toda PR visual sustantiva** antes de mergear.

No es una checklist estética. Es una pregunta repetida 25 veces: *¿este elemento existe porque el contenido real de esta página lo pide, o porque es la salida por defecto de un generador de plantillas?*

## Cómo se usa

Para cada cambio visual sustantivo (nueva familia, rediseño de sección, nuevo componente):

1. Antes de implementar: recorrer la tabla de abajo y marcar qué elementos de la kill-list toca la propuesta.
2. Para cada uno marcado: escribir el **rationale** (por qué este contenido concreto lo necesita) en la propia PR, no en la cabeza de quien lo propuso.
3. Si no hay rationale escrito, el elemento se rechaza. No hay excepción implícita por "queda bien".
4. Un segundo pase (otro agente/humano en rol de crítico, ver `11-SKILLS-Y-AGENTES-PARA-CLAUDE.md`) intenta activamente encontrar el motivo para rechazar, no confirmar la propuesta.

## La kill-list, con criterio de rechazo/aceptación

| # | Elemento | Rechazar cuando... | Aceptar solo si... |
|---|---|---|---|
| 1 | Bento grid | Se usa para agrupar contenido sin relación real de tamaño/jerarquía entre los items, solo por verse "moderno". | El contenido real tiene tamaños de importancia genuinamente distintos y el grid expresa esa jerarquía (ej. una pieza destacada + varias secundarias con datos reales, no placeholders). |
| 2 | Cards uniformes | Todo el contenido —con densidad, longitud y función distintas— se fuerza al mismo contenedor con el mismo padding/sombra/radio. | El contenido es genuinamente homogéneo (ej. lista de herramientas con el mismo contrato) y la card no sustituye una composición editorial posible. |
| 3 | Hero centrado genérico | Título + subtítulo + CTA centrados, sin relación con el contenido específico de esa página. | La página no tiene protagonista visual propio (imagen/dato real) y el centrado es la opción más honesta, no la más rápida. |
| 4 | Badges/pills por todas partes | Se usan como decoración para "romper monotonía" sin que el dato sea realmente una etiqueta/estado. | Representan un estado real y discreto (ej. "Borrador", "Publicado") ya existente en el modelo de datos. |
| 5 | Glassmorphism | Blur + transparencia sin que haya una superficie real detrás que lo justifique. | (No hay caso de aceptación en este proyecto — ver `README.md` línea 102/251, ya excluido explícitamente). |
| 6 | Blobs | Formas orgánicas decorativas sin relación con el contenido. | (No hay caso de aceptación identificado; el proyecto no usa este lenguaje visual). |
| 7 | Gradientes morado/azul | Aparecen como fondo/acento sin relación con la paleta editorial ya definida (ámbar/territorios). | Nunca — la paleta del proyecto está definida en Drive y no incluye esta combinación. |
| 8 | Black/gold "premium" | Se usa como atajo visual para transmitir "calidad" sin relación con la identidad editorial real. | Nunca sin evidencia explícita de que la identidad editorial lo pide (no es el caso actual). |
| 9 | Grano falso | Textura de ruido añadida por CSS/filtro sin relación con material real (papel, tinta). | Existe una referencia editorial real (ej. textura de portada real escaneada) y se usa esa imagen, no un filtro genérico. |
| 10 | Papel sintético | Textura "papel" genérica de stock/IA en vez de fotografía/escaneo real del objeto. | Se usa una fotografía real del libro/objeto físico, con procedencia registrada (`08-ART-DIRECTION-MEDIA-FOTOGRAFIA.md`). |
| 11 | Sombra genérica de SaaS | `box-shadow` de plantilla (offset+blur+opacity por defecto de un generador) sin relación con el sistema de elevación del proyecto. | El proyecto define un sistema de elevación propio (tokens) y la sombra sigue ese sistema, no un valor copiado. |
| 12 | Icono en círculo para cada idea | Se añade un icono decorativo a cada bloque de texto solo por "dar apoyo visual". | El icono transmite información que el texto no da (ej. tipo de contenido) y sustituye texto redundante, no lo acompaña sin función. |
| 13 | Carruseles de contenido principal | Contenido primario (no promocional) se esconde detrás de un carrusel para "caber más". | Es contenido secundario/opcional (ej. reseñas) y el usuario puede ver que hay más sin depender del carrusel para acceder a lo esencial. |
| 14 | Marquee | Texto en movimiento continuo sin que el usuario lo controle. | Nunca — no hay caso de uso editorial que lo justifique en este proyecto. |
| 15 | Parallax continuo | Se aplica a toda la página como efecto por defecto, sin relación con un momento narrativo concreto. | Un momento narrativo puntual y específico lo pide (ej. transición de escena en `las-manecillas-del-recuerdo/`) y se prueba que no perjudica rendimiento/mareo. |
| 16 | Custom cursor | Sustituye el cursor del sistema sin aportar información funcional. | Nunca sin justificación de accesibilidad — el cursor del sistema es información que el usuario ya entiende. |
| 17 | Fade-up en cada sección | Toda sección entra con la misma animación de aparición, independientemente de su contenido. | La animación refuerza un momento narrativo específico y respeta `prefers-reduced-motion`; no es la animación por defecto de cada bloque. |
| 18 | Vídeo hero por impacto | Se añade vídeo de fondo solo para "dar producción" sin que el contenido sea audiovisual. | El vídeo es el contenido real de esa página (ej. intro de Las Manecillas) y no reemplaza texto que el usuario necesita leer. |
| 19 | WebGL sin función | Efecto 3D/shader decorativo sin relación con el contenido ni con una interacción real. | Aporta una interacción o visualización que no es posible con CSS/HTML razonable y se justifica el coste de rendimiento. |
| 20 | Fotografías IA presentadas como realidad | Imagen generada por IA se usa como si fuera una fotografía real del autor/evento/objeto. | Se declara explícitamente como ilustración/generada (nunca sustituye una foto real del autor, portada o evento). |
| 21 | Tipografía enorme como sustituto de composición | Se sube el tamaño de fuente para dar "impacto" en vez de resolver jerarquía real con espaciado/agrupación. | El tamaño responde a una jerarquía tipográfica ya definida (`09-TIPOGRAFIA-RITMO-DENSIDAD.md`), no a una subida puntual sin sistema. |
| 22 | Alternar dos fondos solo para "que se noten secciones" | El único mecanismo de separación entre secciones es un cambio de color de fondo. | El cambio de fondo acompaña una separación de contenido real ya expresada por otros medios (tipografía, espaciado, ritmo — ver "Kill-list" contexto en `README.md`). |
| 23 | Rediseñar todas las familias con el mismo template | Una solución que funcionó en una familia (ej. Home) se copia literalmente a otra (ej. Samuel) sin adaptarse a su contenido/tono propio. | Cada familia mantiene su propia composición derivada de su contenido; los tokens compartidos son de sistema (color/tipografía), no de layout completo. |
| 24 | Componentes de kill-list sin rationale escrito (regla general, `04-FIGMA-MCP-Y-SISTEMA-DE-DISENO.md` línea 440) | La PR no incluye una justificación explícita para el elemento marcado. | Rationale presente y verificable en la propia PR. |
| 25 | Slop de kill-list en la ejecución de una skill (`11-SKILLS-Y-AGENTES-PARA-CLAUDE.md` línea 292) | Un agente/skill introduce alguno de los 24 puntos anteriores como salida por defecto sin que el prompt/tarea lo pidiera. | El agente documenta explícitamente por qué el patrón es la mejor solución para ese contenido concreto. |

## Ejemplos reales de este mismo repositorio (para calibrar, no para copiar)

**Aceptado con rationale** (patrón #12, icono no decorativo): el avatar circular en `autor.html` (`assets/v1-identity.css`, `.masthead-name-row__avatar`) sustituye texto ("foto del autor") por la foto real, no añade un icono genérico junto a texto que ya lo dice.

**Rechazado en revisión durante esta misma tanda** (patrón #17 en potencia): la re-crop del favicon amarillo y las pruebas de tipografía del Abecedario (ver `docs/PENDIENTE-*` y la comparativa enviada al usuario en el chat) se mantuvieron deliberadamente **fuera de producción** hasta tener una decisión explícita del propietario — precisamente para no aplicar un cambio visual sustantivo sin el paso de revisión que este fichero describe.

## Definition of Done de este gate

`DUX-117` se considera aplicado en una PR cuando:

- la PR describe qué elementos de la kill-list toca (aunque sea "ninguno");
- cada elemento tocado tiene rationale escrito en la propia PR, no verbal;
- un segundo pase intentó activamente rechazar la propuesta, no solo confirmarla;
- ninguna de las exclusiones "nunca" de la tabla (filas 5, 6, 7, 8, 14, 16) aparece sin una excepción documentada y aprobada explícitamente por el propietario del proyecto, no por Claude solo.
