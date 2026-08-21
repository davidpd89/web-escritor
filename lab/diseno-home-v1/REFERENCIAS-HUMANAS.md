# 38 — REFERENCIAS HUMANAS + MATRIZ DE TRANSFERENCIA V1

Estado: AUTORITATIVO para inspiración externa del rediseño.
Objetivo: impedir que el implementador rellene huecos con patrones genéricos de IA o con “best practices” sin procedencia.

## Regla

No se copia una web premiada. Se identifica el principio que la hace funcionar y se traduce a una necesidad real de davidportodiaz.com.

Cada referencia tiene uno de cuatro usos:

- **benchmark**: nivel de calidad a superar;
- **principio transferible**: navegación, ritmo, jerarquía, secuencia;
- **código candidato**: solo repositorio público con licencia compatible;
- **API nativa**: preferida cuando permite el mismo resultado con menos deuda.

No se introduce un efecto porque exista una demo. Debe responder a una de estas tareas: orientar, conectar, priorizar, explicar, facilitar una acción o dar continuidad narrativa.

## Referencias seleccionadas

### 1. Webby 2025/2026 — criterios de evaluación
Fuente: https://www.webbyawards.com/judging-criteria/

Transferencia: el gate V1 puntúa por separado contenido, estructura/navegación, diseño visual, funcionalidad, interactividad, innovación y experiencia total. Una Home espectacular no compensa una Herramienta mediocre o una ruta confusa.

### 2. Ottografie / Exo Ape — Webby Winner 2026, Best Navigation/Structure
Fuente: https://winners.webbyawards.com/2026/websites-and-mobile-sites/features-design/best-navigationstructure/363523/ottografie

Transferencia: convertir la amplitud del sitio en un modelo mental visible. Nuestra traducción es la **cartografía editorial**: territorios estables, categorías, recuentos y rutas que el usuario entiende sin abrir megamenús.

NO transferir: piel, fotografía, composición literal o gestos dependientes de hover.

### 3. DICH™ Fashion / BL/S® — Webby Winner 2026, Best User Interface
Fuente: https://winners.webbyawards.com/2026/websites-and-mobile-sites/features-design/best-user-interface/363972/dich-fashion

Transferencia: el estado activo, la transición, la tipografía y la acción forman una sola UI; no existe la separación “contenido bonito + componentes estándar”.

### 4. Webby 2026 — Magazine or Publication
Fuente: https://winners.webbyawards.com/winners/websites-and-mobile-sites/general-desktop-mobile-sites/magazine-or-publication

Ganador: Vogue Business / Archrival: Gen Z Broke The Funnel. Entre los nominados: Field Mag, TIME, The Ring y The Urban Hiking Guide.

Transferencia: Cuaderno, Recomendaciones, Convocatorias y Editoriales deben medirse contra publicaciones/archivos, no contra plantillas de blog.

### 5. Sticky Grid Scroll — Theo Plawinski / Codrops
Tutorial: https://tympanus.net/codrops/2026/03/02/sticky-grid-scroll-building-a-scroll-driven-animated-grid/
Repo: https://github.com/theoplawinski/codrops-sticky-grid-scroll
Licencia del repo verificada: MIT.

Principio humano útil: ritmo + espacio + progresión dentro de una escena fija; el scroll se trata como tiempo.
Transferencia V1: una única escena opcional de archivo/prensa con elementos documentales que se ordenan, no un grid de cards.
Restricción: NO cargar GSAP/Lenis globalmente. La V1 estática debe funcionar sin esta escena. Si se reutiliza código literal, conservar aviso MIT.

### 6. SVG Mask Transitions on Scroll — Hiroki Watanabe / Codrops
Tutorial: https://tympanus.net/codrops/2026/03/11/svg-mask-transitions-on-scroll-with-gsap-and-scrolltrigger/
Repo: https://github.com/Hiro-kiii/Scroll-Transition
Licencia del repo verificada: MIT.

Principio humano útil: una transición debe expresar cambio de escena, no ser adorno.
Transferencia V1: como máximo una máscara/seam narrativa en una página de obra o campaña; nunca sobre texto crítico ni navegación.

### 7. Curved Path — Ross Anderson / OFF+BRAND
Fuente: https://tympanus.net/codrops/2025/12/17/building-responsive-scroll-triggered-curved-path-animations-with-gsap/

El caso nace del sitio de Lando Norris y resuelve una curva entre posiciones que se recalculan responsive. El propio tutorial documenta reduced-motion y un configurador visual para fijar los puntos finales.

Transferencia V1: la **ruta viva** se calcula a partir de anclas reales del layout, no de coordenadas mágicas. En reduced-motion se muestra completa y estática.

### 8. View Transition API — MDN
Fuente: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API
Uso MPA: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using

Transferencia V1: continuidad Home→Manecillas y, más tarde, índice de Cuaderno→artículo. Mismo origen, opt-in MPA, sin convertir la web en SPA. Si no hay soporte, la navegación normal es el fallback.

### 9. CSS scroll-driven animations — MDN
Fuente: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline

Estado actual: soporte todavía limitado/no Baseline para `animation-timeline`.
Transferencia V1: solo enhancement detrás de `@supports`; nunca única implementación.

## Lo que esta investigación descarta

- convertir la web completa en una experiencia WebGL;
- Three.js/WebGPU como infraestructura global;
- smooth-scroll obligatorio;
- scroll-jacking;
- cursor personalizado;
- ruido/grano/blur/glass como identidad;
- mosaicos de cards;
- bento;
- contadores/KPI corporativos;
- dark mode como firma principal;
- animar cada aparición;
- iconografía “mágica” o relojes decorativos inventados.

## Regla de originalidad

La originalidad V1 sale de **repetir pocas firmas propias en contextos distintos**:

1. coordenada/folio;
2. línea cartográfica;
3. ledger editorial;
4. objeto-libro;
5. seam entre territorios;
6. archivo que se despliega.

Si una nueva idea no pertenece a una de esas familias, no entra sin revisión.

## Segunda pasada — casos humanos que endurecen el sistema

### 10. Reform Collective — «A New Website, Designed to Be Seen»
Fuente: https://tympanus.net/codrops/2025/07/24/reform-collective-a-new-website-designed-to-be-seen/

Transferencia: claridad, rendimiento y estructura antes que espectáculo. Una escena CSS expresiva puede existir sin convertir todas las páginas en una demo.
NO transferir: su piel de estudio, su navegación concreta o el efecto 3D como firma global.

### 11. Spain Collection — digital ecosystem
Fuente: https://tympanus.net/codrops/2025/12/18/spain-collection-evolving-a-luxury-website-into-a-digital-ecosystem/

Transferencia: diseño editorial, aire, arquitectura de contenido explícita y momentos memorables pero sutiles. Es especialmente útil para confirmar que familias con necesidades distintas pueden tener composición propia dentro de un sistema común.
NO transferir: estética de lujo/viajes, dependencia de fotografía masiva ni modales de catálogo sin necesidad funcional.

### 12. Exat Microsite — Studio Size
Fuente: https://tympanus.net/codrops/2026/04/10/the-exat-microsite-pushing-a-typography-showcase-to-new-creative-extremes/

Transferencia: la tipografía puede ser interfaz; alternar tramos calmados y expresivos evita fatiga. El scroll estructura el tiempo, no sirve de excusa para animar todo.
NO transferir: efectos de specimen tipográfico ni movimiento continuo como portador de información.

### 13. Christian Fleming — proceso print/web/3D
Fuente: https://tympanus.net/codrops/2025/08/14/setting-the-stage-inside-the-process-of-bringing-christian-flemings-work-to-life-in-print-web-and-3d/

Transferencia: probar títulos largos y móvil desde las primeras iteraciones; resolver jerarquía con posición, peso y espacio antes de añadir contenedores.
NO transferir: la piel teatral ni la puesta en escena fotográfica literal.

### 14. 24/7 Artists — storyboard antes de UI
Fuente: https://tympanus.net/codrops/2025/04/16/case-study-24-7-artists/

Transferencia: para una página larga y narrativa, storyboard de escenas/estados/transiciones antes de programar. Priorizar recursos visuales fuertes que el equipo sabe ejecutar y mantener.
NO transferir: mouse trails, visualizadores musicales o espectáculo full-screen que no ayude a leer/navegar.

## Consecuencia para V1

Estas referencias no añaden cinco efectos. Refuerzan tres decisiones: **tipografía como interfaz**, **pacing editorial por escenas** y **espectáculo aislado con fallback estático completo**. Si una propuesta no mejora esas tres cosas o la orientación del usuario, se descarta.


## Absorción Perplexity 1 — recursos externos auditados

### 15. Stripe Press
Fuente: https://press.stripe.com/
Transferencia: una ficha de obra deja comprender y leer antes de presionar compra. Valida Book Master: obra → copy editorial → fragmento → disponibilidad. No transferir truncado automático del fragmento.

### 16. MagCulture
Fuente: https://magculture.com/
Transferencia: jerarquía por escala/proporción desigual, útil en Home/Obras/Cuaderno. No convertirlo en grid/card universal.

### 17. Brutalist Web Design — affordance de links
Fuente: https://brutalist-web.design/
Transferencia: los enlaces de prosa deben parecer enlaces; confirma underline/regla visible del contrato global.

### 18. Perplexity — recursos revisados y NO adoptados
- Lenis: no; scroll nativo.
- GSAP/ScrollTrigger: no V1 sin necesidad funcional probada.
- Motion: no dependencia sin caso.
- CSS scroll-driven: mecanismo condicional para visual no esencial; no fade-up universal.
- Fontshare Zodiak/Sentient/General Sans/Satoshi: no reabrir stack antes de render real.
- Godly word reveal/custom cursor/horizontal scroller/count-up: rechazados.
- DALL·E/assets sintéticos, Lottie loader, vídeo hero: rechazados por procedencia/anti-IA.
- breakpoints por dispositivos y `max-width:1200px` global: rechazados; romper por contenido.
- byte caps universales: no sin baseline medido.

Refuerzo técnico aceptado: nunca `transition: all`; si alguna animación JS futura existe, debe inicializarse/cancelarse conforme a `prefers-reduced-motion` incluso cuando la preferencia cambia con la página abierta.
