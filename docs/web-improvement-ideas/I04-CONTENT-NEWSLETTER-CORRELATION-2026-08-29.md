# I.4 · Correlación contenido → newsletter/acción, manual-first

**Estado histórico final de PR #135:** `IMPLEMENT_AFTER_CURRENT_DEBT`  
**Dirección intermedia de la matriz:** `IMPLEMENTAR MANUAL FIRST`  
**Regla:** usar primero datos agregados y exports existentes; no crear un tracker nuevo ni un identity graph entre analítica y Brevo.

## 1. Hipótesis original

I.4 proponía un dashboard interno para entender qué contenidos generan más suscripciones/acciones, cruzando manualmente los datos que ya recogen las herramientas actuales.

La parte valiosa de la idea no era el “dashboard”. Era responder preguntas como:

- qué familias de contenido preceden más altas;
- qué campañas/editoriales llevan visitas útiles;
- qué fuentes de suscripción (`SOURCE`) convierten mejor en términos agregados;
- qué contenido merece más distribución o una mejor CTA.

#135 fue endureciendo la propuesta hasta eliminar la necesidad de un sistema nuevo de tracking.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Cruce interno contenido↔newsletter↔club con datos existentes. |
| Revisión 108/108 | `IMPLEMENT_AFTER_CURRENT_DEBT` | Aprovechar `SOURCE`; reporting agregado; no identity graph. |
| Matriz operativa | `IMPLEMENTAR MANUAL FIRST` | CSV/exports/UTM primero; otro tracker solo si existe un gap demostrado. |
| Autoridad final | `IMPLEMENT_AFTER_CURRENT_DEBT` | Sí aporta, pero después de cerrar deuda actual de Brevo/privacidad. |
| Revalidación independiente | mantenido | No aparece necesidad de behavioral tracker adicional; Clarity no se instala por defecto. |

`IMPLEMENTAR MANUAL FIRST` y `IMPLEMENT_AFTER_CURRENT_DEBT` son compatibles: la capacidad merece existir, pero **su primera versión no debe ser una feature web ni un pipeline de identidad**.

## 3. Estado real de `main` al 29/08/2026

`main@291c8c677aaa7df635142687d1a6848e80ffcaa2` ya ofrece piezas suficientes para una primera correlación agregada:

### Newsletter / Brevo

El navegador envía al Worker un contrato mínimo:

```text
email + source + website(honeypot) [+ result acotado para quiz]
```

El Worker convierte `source` a un atributo Brevo `SOURCE` server-side.

Fuentes conocidas incluyen:

- `home`;
- `fragmento`;
- `manecillas`;
- `cuaderno`;
- `popup`;
- `explore`;
- `quiz`;
- `lectores-beta` en lista separada.

Importante: **`SOURCE` identifica el punto/tipo de captación, no necesariamente el artículo exacto que precedió al alta**. No inflar su granularidad hasta convertirlo en historial de navegación.

### Analítica

El runtime tiene GoatCounter y Metricool y eventos custom para acciones concretas. La política actual mantiene una postura deliberadamente ligera de tracking.

### Email campaigns

`docs/brevo/04-CAMPANAS-AUTOMATIZACIONES-Y-CONTENIDO.md` ya propone una taxonomía de campañas y UTMs:

- `utm_source=brevo`;
- `utm_medium=email`;
- `utm_campaign=<slug-estable>`;
- `utm_content` cuando sea útil.

Por tanto I.4 debe **reutilizar estas señales**, no inventar otra nomenclatura.

## 4. Deuda previa que bloquea la implementación

Antes de convertir I.4 en un reporting estable hay que cerrar/confirmar:

1. **I.2/E.8:** inventario real de analítica/terceros y contrato de privacidad.
2. **H.1/H.2:** journeys/segmentación de Brevo con evidencia E2E, no solo diseño documental.
3. La incongruencia actual entre política y formularios generales sobre la casilla de consentimiento debe resolverse en su autoridad correspondiente.
4. Baseline real de datos disponibles: no asumir que cada panel/export conserva la dimensión necesaria.

I.4 no debe ser el motivo para añadir nuevos identificadores antes de cerrar esos gaps.

## 5. Preguntas que I.4 sí puede responder

Ejemplos válidos:

- ¿Cuaderno, ficha de Manecillas o fragmento genera más solicitudes DOI por cada 1.000 visitas?
- ¿Qué campaña Brevo envía tráfico que luego navega hacia una obra/fragmento?
- ¿Un artículo concreto que recibe distribución externa produce un aumento agregado de altas durante su ventana?
- ¿Las CTAs del Cuaderno merecen más prominencia o menos?

Ejemplos que I.4 **no** necesita responder:

- “¿Qué leyó exactamente esta persona antes de suscribirse?”
- “¿Qué contacto de Brevo visitó después esta URL?”
- “Construye el perfil individual de intereses de cada lector a partir de toda su navegación.”

Esas preguntas cambian radicalmente privacidad, tracking y arquitectura y no están autorizadas por #135.

## 6. Primera implementación correcta: manual-first

### Paso 1 — definir periodo y pregunta

Ejemplo:

```text
Ventana: 2026-09-03 → 2026-09-30
Pregunta: qué superficies públicas generan más solicitudes DOI confirmables.
```

### Paso 2 — exportar/agrupar fuentes existentes

Sin PII:

- páginas/sesiones/referrers relevantes desde analítica;
- conteos de solicitudes/altas por `SOURCE` desde Brevo cuando el export/panel lo permita;
- UTMs de campañas;
- eventos custom de CTAs ya existentes;
- resultados de campaña agregados.

### Paso 3 — normalizar una tabla pequeña

Ejemplo conceptual:

| periodo | superficie | visitas | CTA | DOI/altas agregadas | fuente | notas |
|---|---|---:|---:|---:|---|---|
| ... | Manecillas | ... | ... | ... | `SOURCE=manecillas` | campaña lanzamiento |

No incluir emails, IDs de contacto o timelines individuales.

### Paso 4 — decisión

El informe debe terminar en una acción:

- mantener;
- mover CTA;
- mejorar copy;
- reforzar distribución;
- retirar una superficie;
- `NO_CHANGE` por falta de muestra.

Un dashboard que no cambia decisiones es precisamente lo que I.1/I.3 intentan evitar.

## 7. Granularidad: no convertir `SOURCE` en tracking invasivo

Es tentador sustituir `cuaderno` por `cuaderno-articulo-123` en cada alta. No hacerlo automáticamente.

Antes de aumentar granularidad:

- demostrar que la pregunta no puede resolverse con UTM/referrer/evento agregado;
- revisar privacidad y retención;
- evitar valores libres controlados por cliente;
- mantener allowlist server-side;
- asegurar que no se construye un historial individual.

La frontera del Worker actual —`source` acotado y mapping server-side— es una propiedad de seguridad que debe conservarse.

## 8. No crear otro tracker

I.4 explícitamente prefiere:

1. exports/panel;
2. CSV local;
3. unión agregada por periodo/superficie/campaña;
4. automatización posterior solo si la tarea se vuelve repetitiva y estable.

No instalar por I.4:

- Google Analytics;
- Brevo Tracker;
- Clarity behavioral tracking;
- customer data platform;
- fingerprinting;
- identity resolution.

## 9. Posible automatización futura

Solo si el reporting manual demuestra valor repetido:

- script read-only que reciba exports ya desidentificados;
- esquema versionado del reporte;
- validación de columnas;
- salida CSV/Markdown/JSON agregada;
- cero credenciales en repo;
- sin datos personales en fixtures;
- sin joins por email/hash de email.

No hace falta una aplicación web ni un “dashboard” para cerrar I.4.

## 10. Relación con otras ideas

- **H.1/H.2:** primero demostrar journeys y segmentación reales.
- **H.5:** no hacer inferencia estadística con muestras ridículas.
- **I.2/E.8:** inventario de terceros y finalidad de cada señal.
- **I.3:** nuevas métricas solo ante pregunta concreta.
- **I.5:** revisar periódicamente si cada campo/evento sigue siendo necesario.
- **Q.3:** experimentos de CTA/distribución deben registrarse con baseline/ventana.

## 11. Definition of Done de la primera versión

- [ ] deuda Brevo/privacidad previa cerrada o explícitamente no bloqueante;
- [ ] pregunta decisional definida;
- [ ] UTMs/taxonomía existentes reutilizadas;
- [ ] `SOURCE` interpretado como origen de captación, no historial completo;
- [ ] datos agregados, sin email/ID de contacto;
- [ ] no se instala tracker adicional;
- [ ] tabla/reporte reproducible para una ventana;
- [ ] se documentan limitaciones de atribución;
- [ ] hay decisión o `NO_CHANGE` explícito;
- [ ] automatización solo después de demostrar repetición/valor.

## 12. Trazabilidad #135

Revisados:

- banco original I.4;
- revisión 108/108: `IMPLEMENT_AFTER_CURRENT_DEBT`, `SOURCE` y no identity graph;
- matriz final: `IMPLEMENTAR MANUAL FIRST`, CSV/exports;
- repo cross-check y overrides;
- blueprints: privacidad/third-party comparte autoridad con I.2/E.8;
- autoridad machine-readable;
- autoridad humana final: `IMPLEMENT_AFTER_CURRENT_DEBT`;
- revalidación independiente: estados I mantenidos, tracking comportamental no abierto por defecto.

## 13. Cierre

I.4 sí tiene valor porque conecta contenido con resultados. Su diseño correcto es deliberadamente aburrido: **señales que ya existen + agregación + una pregunta + una decisión**. Solo después de demostrar uso repetido tendría sentido automatizar el informe; nunca construir primero un grafo de lectores.