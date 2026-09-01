# D.3 · Progreso de lectura visible en artículos largos

Fecha de reconstrucción: 2026-08-29  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `PARTIAL_AUDIT`.  
Revalidación actual: la capacidad sigue existiendo en `script.js` mediante opt-in `data-reading-progress`; no construir otra barra.

## 1. Hipótesis original

Añadir una barra de progreso de scroll en artículos largos de `cuaderno/`, presentada inicialmente como patrón de bajo coste y alto valor percibido, con cuidado especial de no introducir CLS.

## 2. Evolución histórica

### Primera revisión → `CONDITIONAL`

#135 reduce la confianza inicial:

- la barra no resuelve por sí sola un problema demostrado;
- solo pilotar en artículos largos;
- debe existir investigación/señal de uso;
- cero CLS.

### Matriz → `DEFERIR/PILOTAR`

La matriz añade un riesgo móvil:

> progreso solo si artículos largos y usuarios lo necesitan; sticky UI puede empeorar móvil.

### Repo cross-check → `PARTIAL_AUDIT`

La inspección profunda cambia materialmente el estado: `script.js` ya contenía runtime `[data-reading-progress]`.

La pregunta dejó de ser «¿lo construimos?» y pasó a ser:

- ¿en qué páginas se monta?;
- ¿solo en long-form adecuado?;
- ¿introduce CLS?
- ¿aporta valor real?

### Autoridad final → `PARTIAL_AUDIT`

`PR135-FINAL-AUTHORITY-2026-08-28.md` cierra:

> «Barra de progreso solo si artículos largos y prueba de usuario la justifican; evitar sticky UI gratuita.»

### Revalidación independiente

D.1–D.12 se mantienen; no hay override para reconstruir la feature.

## 3. Implementación real localizada

El runtime actual es opt-in:

```js
if (!document.body.hasAttribute("data-reading-progress")) return;
```

Después:

- crea `.reading-progress`;
- la inserta al inicio de `body`;
- escucha `scroll` de forma pasiva;
- difiere cálculo mediante `scheduleTask`;
- calcula `scrollY / (scrollHeight - innerHeight)`;
- actualiza el ancho.

No se inyecta en todas las páginas. El comentario del propio código define el contrato: long-form reading pages optan explícitamente; utilities/tools/legal no.

## 4. Qué significa `PARTIAL_AUDIT`

No significa «la barra está mal» ni «hay que terminarla».

Significa:

```text
capacidad existente
+ montaje selectivo
+ utilidad no universalmente demostrada
= auditar antes de tocar
```

## 5. Auditoría correcta

Inventario por ruta:

```text
URL
word_count / estimated length
has data-reading-progress
article/fragment/tool/etc.
mobile header/sticky collisions
CLS before/after
keyboard/focus impact
user/research justification
```

Resultado por URL:

```text
KEEP
REMOVE
ADD
NO_ACTION
```

No convertir el atributo en requisito de todas las páginas editoriales.

## 6. UX móvil

La barra debe evitar:

- competir con header sticky;
- tapar foco o contenido;
- crear una segunda línea sticky innecesaria;
- consumir altura útil de móvil;
- interpretar scroll corto como «progreso de lectura» significativo.

Una pieza de 600 palabras no necesita necesariamente un indicador continuo.

## 7. Accesibilidad

El código actual usa `role="progressbar"` pero `aria-hidden="true"`, tratándolo como señal visual secundaria. Si sigue siendo puramente decorativo/informativo no esencial, esa decisión evita anuncios continuos molestos.

No convertirlo en live region.

Si en el futuro se expone semánticamente el progreso, habría que gestionar `aria-valuenow`, frecuencia de actualización y utilidad real para AT; no hacerlo por automatismo.

## 8. CLS y rendimiento

Gate de D.3:

- reservar/overlay sin desplazar layout;
- listener pasivo;
- no medir/forzar layout repetidamente de manera costosa;
- no cargar dependencia;
- comprobar INP/scroll performance en móvil.

El runtime actual ya intenta minimizar coste con scheduling; cualquier refactor debe medirse.

## 9. Relación con D.9

D.3 responde «cuánto he avanzado». D.9 responde «cuánto tardaré aproximadamente».

No son obligatoriamente un pack. Un artículo puede beneficiarse de uno y no del otro.

## 10. Relación con D.2

No hace falta Reader Mode para tener progreso. La barra debe funcionar sobre la composición normal y no justificar un modo de lectura paralelo.

## 11. Relación con I.3

I.3 propone scroll depth agregado para analítica. Eso es medición interna; D.3 es UI. No añadir tracking solo porque exista una barra visual.

## 12. Qué NO hacer

- otra barra nueva/componente paralelo;
- sticky UI en todas las páginas;
- `aria-live` con porcentaje en cada scroll;
- asociar progreso de scroll con lectura real exacta;
- convertirlo en KPI de engagement;
- añadirlo a herramientas/legal/home por consistencia visual;
- rehacer el runtime sin fallo reproducible.

## 13. Trigger para cambios futuros

Solo modificar si aparece al menos uno:

- artículo largo sin atributo donde testing demuestra utilidad;
- página corta donde la barra molesta;
- CLS/overlap reproducible;
- performance issue;
- problema de contraste/visibilidad;
- investigación de usuario que pida/elimine el patrón.

## 14. Pasadas posteriores revisadas

Cuarta–decimoquinta: no cambian D.3. R.12 recuerda medir LoAF/INP antes de tocar scheduling; R.13 puede afectar contraste visual si existe un problema comprobado. Ninguno ordena expandir la barra.

## 15. Trazabilidad

- idea original — barra de scroll;
- revisión — `CONDITIONAL`;
- matriz — `DEFERIR/PILOTAR`;
- `IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — runtime existente y cambio a `PARTIAL_AUDIT`;
- autoridad final — `PARTIAL_AUDIT`;
- revalidación independiente — mantenida;
- `script.js` actual — implementación opt-in confirmada.

## 16. Definition of Done de esta reconstrucción

- [x] evolución de estado completa;
- [x] implementación existente identificada;
- [x] no se propone segunda barra;
- [x] gates móvil/CLS/a11y/performance preservados;
- [x] alcance de auditoría definido.

## Recomendación para Clara/Claude

No implementar D.3 desde cero. Auditar el montaje actual de `data-reading-progress` y corregir únicamente evidencia concreta.