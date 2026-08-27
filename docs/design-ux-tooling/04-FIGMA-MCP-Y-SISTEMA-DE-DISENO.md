# 04 — Figma MCP y sistema de diseño operativo

## 1. Papel de Figma en este proyecto

Figma no sustituye al navegador y no es una segunda fuente de verdad del producto.

Su función es crear un espacio donde podamos:

- estudiar la composición actual;
- comparar familias;
- explorar alternativas antes de tocar código;
- documentar jerarquía por viewport;
- revisar media/crops;
- visualizar tokens y relaciones;
- conservar rationale;
- enseñar a Claude un diseño concreto en lugar de describirlo con un prompt ambiguo.

El navegador sigue siendo la autoridad sobre:

- HTML real;
- responsive real;
- fuentes renderizadas;
- viewport;
- performance;
- interacción;
- accesibilidad;
- estado final.

## 2. Conexión recomendada

MCP remoto oficial:

```text
https://mcp.figma.com/mcp
```

Claude Code, preferencia:

```bash
claude plugin install figma@claude-plugins-official
```

Alternativa MCP manual:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

Autenticación: OAuth.

No almacenar tokens OAuth en `.env`, Markdown, commits o configuración compartida del repo.

## 3. Modelo de fichero Figma

Crear un fichero de trabajo específico para la web, separado de assets promocionales.

Estructura propuesta:

### `00 — README / DECISION LOG`

- objetivo;
- Drive docs de autoridad;
- kill-list;
- viewport matrix;
- estado de cada familia;
- enlaces a PR/evidence.

### `01 — FOUNDATIONS (READ-ONLY BASELINE)`

- tokens actuales;
- stack tipográfico;
- gutter;
- spacing;
- focus;
- líneas;
- superficies;
- tamaños de control;
- ejemplos reales de componentes.

No reinterpretarlos todavía.

### `02 — CURRENT SNAPSHOTS`

Frames con capturas reales de producción/preview:

- Home;
- Manecillas;
- Samuel;
- Autor;
- Cuaderno;
- artículo;
- Herramientas;
- herramienta;
- Prensa;
- Eventos;
- directorio.

Cada una en 390, 768 y 1440 como mínimo.

### `03 — MOBILE HIERARCHY LAB`

Exploraciones centradas en 390 y 320.

No diseñar primero 1440 y «hacer responsive» después.

### `04 — BOOK FAMILY`

Manecillas, Samuel y estado neutro para obra futura.

### `05 — IDENTITY FAMILY`

Autor, premios, prensa, eventos.

### `06 — EDITORIAL FAMILY`

Cuaderno, tema, artículo, recomendaciones.

### `07 — TOOLS / RESOURCES`

Hub y herramienta abierta; directorios.

### `08 — SHELL / EXPLORAR`

Solo si existe una mejora demostrada respecto a lo ya implementado.

### `09 — MEDIA / CROPS`

Focal points y encuadres por breakpoint.

### `10 — APPROVED REDLINES`

Únicamente decisiones aprobadas para implementación.

## 4. Frames obligatorios

No usar nombres de dispositivo como autoridad. Los frames son puntos de observación.

Mínimos:

- 320;
- 390;
- 768;
- 1024;
- 1440;
- 1728;
- landscape bajo cuando la familia lo necesita.

Para una exploración temprana se puede trabajar 390 + 1440, pero no aprobarla sin los demás estados.

## 5. Cómo introducir la web actual en Figma

No reconstruirla de memoria.

Flujo:

1. Playwright captura la URL real;
2. guardar screenshot + viewport + commit SHA;
3. colocar captura en `CURRENT SNAPSHOTS`;
4. anotar problemas encima, sin redibujar aún;
5. consultar DOM/computed styles con DevTools;
6. registrar qué reglas provocan la geometría;
7. crear variantes junto al baseline.

La captura debe indicar:

```text
URL
commit SHA
fecha
viewport
browser
estado (default/focus/open/result/etc.)
```

## 6. Variantes de diseño

Para decisiones no triviales, Claude debe producir 2–3 hipótesis, no veinte.

Cada variante se formula como hipótesis:

### Mala etiqueta

`Variante bonita`

### Buena etiqueta

`B — mantiene H1, adelanta portada y crea cierre de sinopsis mediante cambio de medida`

Cada variante incluye:

- problema que resuelve;
- variables que cambia;
- variables que preserva;
- coste técnico estimado;
- riesgo SEO/a11y/performance;
- comportamiento mobile/desktop.

## 7. Figma no debe inventar contenido

Los frames utilizan:

- copy real;
- imágenes reales;
- metadatos reales;
- textos de longitud real;
- estados reales.

No usar lorem ipsum para validar composición final.

Razón: la geometría del sitio depende de títulos largos en español, nombres, fechas, ISBN, enlaces y contenido real.

## 8. Tokens: read first

La primera conexión Figma ↔ repo es de **lectura y comparación**.

No permitir un flujo:

```text
Figma cambia variable → Claude sobrescribe CSS automáticamente
```

sin revisión.

La auditoría debe generar un mapa:

| Concepto | CSS actual | Figma | Drift | Acción |
|---|---|---|---|---|
| gutter | token | variable/frame | sí/no | mantener/revisar |
| reading measure | token | layout | sí/no | ... |
| font display | token | style | sí/no | ... |
| section spacing | token | spacing | sí/no | ... |

## 9. Componentes de diseño que sí tienen sentido

No hacer un catálogo de 100 componentes para una web editorial pequeña.

Agrupar por **gramática**, no por cada pieza HTML.

### Fundaciones

- text styles;
- line styles;
- surfaces;
- spacing;
- focus;
- media rules.

### Shell

- header;
- Explorar;
- footer;
- breadcrumbs;
- global actions.

### Editorial

- section head;
- ledger row;
- metadata group;
- pull quote;
- note;
- source list;
- related route;
- figure/caption;
- route/filet.

### Objetos

- book cover treatment;
- author portrait;
- event/document image.

### Functional

- field;
- result region;
- status;
- filter/control;
- primary/secondary action.

No crear `Card`, `Card2`, `Card3` como unidad universal.

## 10. Code Connect — decisión condicional

Code Connect es útil cuando existe correspondencia estable entre componentes Figma y componentes de código.

El proyecto actual es HTML/CSS estático con familias específicas. Por tanto:

- no migrar a React;
- no crear wrappers ficticios;
- no hacer componentization únicamente para habilitar una integración.

Reabrir si el código evoluciona hacia componentes reales con API estable.

## 11. Uso de Agent Skills de Figma

Cuando el plugin oficial incluya Skills adecuados, preferirlos a un superprompt de diseño genérico.

Claude debe seguir la secuencia:

```text
contexto del frame
→ inspección de propiedades
→ intención del contrato Drive
→ tarea pequeña
→ resultado en canvas
→ review independiente
```

No:

```text
"rediseña esta web para hacerla premium"
```

## 12. Anotaciones de decisión

Cada cambio aprobado debe tener una nota breve:

```yaml
id: DUX-042
family: article
viewport: mobile
problem: secciones H2 no tienen corte perceptual
change: alternar medida/espacio y tratamiento de figura; no añadir cards
preserves:
  - URL/DOM headings
  - Newsreader body
  - current color tokens
validated_by:
  - Playwright capture
  - axe/Stark
  - BrowserStack iOS
status: approved-for-code
```

Puede mantenerse como comentario de Figma + registro en repo.

## 13. Redlines útiles

Redline no significa especificar cada pixel de una captura.

Debe documentar relaciones que importa preservar:

- medida de texto;
- distancia entre ancla/cuerpo;
- zona de media;
- gutter/full-bleed;
- orden;
- break condition;
- crop;
- alineación;
- máximo/mínimo razonable.

Evitar convertir un diseño responsive en coordenadas absolutas.

## 14. Diseño de mobile primero en los problemas mobile

Si el bug es «mobile plano», el lab empieza en 390.

Workflow recomendado para una familia:

1. capturar 390 actual;
2. marcar escenas;
3. identificar qué relaciones desktop desaparecen;
4. diseñar tres maneras de reconstruirlas en mobile;
5. elegir una;
6. comprobar 320;
7. escalar a 768;
8. verificar que desktop no pierde identidad;
9. implementar.

## 15. Figma y media

Los crops aprobados deben guardar:

- asset id/path;
- breakpoint;
- focal point;
- ratio;
- contexto;
- si admite recorte;
- si requiere imagen alternativa.

No decidir `object-position` por tanteo repetido en CSS sin registrar la intención.

## 16. Handoff a código

Claude recibe para cada cambio:

- URL/familia;
- frame aprobado;
- before/after;
- reglas de composición;
- breakpoints por contenido;
- assets existentes;
- restricciones;
- acceptance criteria.

La implementación debe ser pequeña. Evitar un PR de «rediseño de toda la web».

Orden preferido:

1. pilot family;
2. validar;
3. extraer patrón reutilizable si existe;
4. siguiente familia.

## 17. Review independiente

El mismo agente que genera una variante no debe ser su único juez.

Usar un segundo pase/agent con rol de crítico que reciba:

- contrato 16/17;
- baseline;
- propuesta;
- kill-list;
- constraints.

Y pregunte:

- ¿qué problema resuelve realmente?;
- ¿qué se ha añadido sin necesidad?;
- ¿parece un patrón de IA?;
- ¿se ha degradado lectura?;
- ¿mobile es composición propia?;
- ¿hay otra solución más sobria?;

## 18. Definition of Done de un frame

Un frame no está aprobado hasta que:

- usa contenido real;
- especifica viewport;
- expresa protagonista;
- las escenas se distinguen;
- no depende de color exclusivamente;
- no introduce componentes de kill-list sin rationale;
- contempla estados interactivos relevantes;
- tiene respuesta mobile/desktop;
- media tiene procedencia/crop definido;
- puede implementarse con HTML/CSS progresivo razonable;
- se ha revisado contra a11y y performance antes de entrar a código.

## 19. Regla final

Figma es un **instrumento para pensar con precisión**.

Si su uso hace que Claude produzca más rápido una plantilla genérica, se está usando mal. Si hace visibles las relaciones, permite comparar alternativas y deja trazabilidad de por qué una composición existe, está cumpliendo su función.