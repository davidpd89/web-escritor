# 02 — Arquitectura Reader CRM

**Objetivo:** usar Brevo como memoria estructurada de la relación con lectores sin convertir la base de datos en un almacén de datos innecesarios.

---

## 1. Qué significa Reader CRM en este proyecto

No buscamos un CRM de ecommerce clásico. La relación principal es editorial.

Un contacto puede estar en uno o varios contextos:

- lector interesado en novedades;
- lector de Manecillas;
- lector de Samuel/Noveris;
- lector del Cuaderno;
- escritor que usa herramientas/recursos;
- lector beta;
- periodista/medio;
- librería/biblioteca;
- club de lectura;
- organizador de evento;
- colaborador profesional.

Brevo debe ayudarnos a recordar **lo que la persona ha pedido o expresado**, no a inferir perfiles invasivos.

---

## 2. Modelo de listas

### Regla

**Lista = pertenencia estable o frontera de propósito.**  
**Segmento = selección dinámica para trabajar/enviar.**

Brevo convirtió las antiguas listas dinámicas en listas estáticas en 2025 y recomienda usar segmentos para comportamiento y filtros dinámicos.

### Listas recomendadas

#### `Lectores web`

Estado conocido: lista canónica, históricamente ID 3.

Propósito:

- newsletter/novedades generales del autor.

Debe poder contener suscriptores llegados de home, popup, explore, Cuaderno, fragmentos, Manecillas o quiz siempre que el consentimiento mostrado sea el mismo propósito general.

#### `Lectores beta`

Propósito distinto:

- recibir material no publicado;
- participar en lecturas beta;
- recibir solicitudes de feedback relacionadas.

No implica newsletter general.

#### Otras listas

No crear por defecto:

- `Home`;
- `Popup`;
- `Cuaderno`;
- `Quiz`;
- `Manecillas`;
- `Samuel`;
- `Mensajero`;
- etc.

Esos son atributos/segmentos, no fronteras de consentimiento.

### Contactos profesionales

No crear una lista de marketing `Prensa` simplemente para mandar newsletters.

Usar:

- Contacts/Companies;
- Deals;
- pipeline profesional;
- notas/tareas;
- comunicaciones 1:1 o campañas específicas solo cuando exista base adecuada.

---

## 3. Modelo de atributos

### Ya existente

#### `SOURCE`

Mantener.

Valores actuales controlados server-side:

- `home`
- `fragmento`
- `manecillas`
- `cuaderno`
- `popup`
- `explore`
- `quiz-noveris`
- `lectores-beta`

No aceptar free text desde navegador.

#### `NOVERIS`

Mantener como categoría/enumeración si el atributo real está configurado así.

Valores:

- `mensajero`
- `sabio`
- `silenciadora`
- `guardian`

### Atributos futuros recomendados solo si hay un uso real

#### `INTERESTS`

Tipo preferible: multi-select.

Valores potenciales:

- `manecillas`
- `samuel-noveris`
- `cuaderno`
- `herramientas-escritores`
- `eventos`

Crear solo cuando haya un mecanismo explícito para que el usuario los seleccione o una regla editorial muy clara. Si Consent Groups está habilitado y encaja mejor, evitar duplicar preferencias en un atributo paralelo.

#### `LANGUAGE`

No necesario mientras todas las comunicaciones sean esencialmente ES. Crear si se introduce contenido multilingüe real.

#### `FIRSTNAME`

No añadir a los formularios actuales solo por personalización de saludo. Cada campo extra añade fricción.

Se puede recopilar:

- en preference center;
- en Meetings;
- en CRM profesional;
- cuando el beneficio sea claro.

#### Datos de consentimiento

Antes de crear manualmente `CONSENT_*`, revisar:

- prueba de DOI disponible en Brevo;
- Consent Groups;
- historial del contacto;
- atributos de consentimiento de tracking administrados por Brevo.

No mantener dos sistemas inconsistentes para la misma verdad.

### Nunca como atributo de marketing

- diagnósticos o datos sensibles;
- información inferida sobre religión, política, salud, orientación, etc.;
- notas privadas que no deberían salir del contexto profesional;
- texto completo de mensajes personales;
- password/tokens/secrets;
- datos comprados/scrapeados.

---

## 4. Consent Groups — arquitectura propuesta

Brevo añadió API oficial de Consent Groups en 2026. La funcionalidad puede no estar activada para todas las cuentas.

### Si está disponible

Crear un conjunto pequeño y comprensible, por ejemplo:

1. **Novedades de libros**
   - lanzamientos;
   - fragmentos/novedades relevantes;
   - disponibilidad confirmada.

2. **Cuaderno y recursos**
   - nuevos artículos;
   - herramientas/recursos destacados;
   - recopilaciones ocasionales.

3. **Eventos y encuentros**
   - presentaciones;
   - firmas;
   - clubes/ferias donde participe el autor.

No crear 15 grupos granulares. El preference center debe ser entendible en segundos.

### Lectores beta

Mantener **además** la separación de lista/purpose.

Un Consent Group puede complementar el control de preferencias si la funcionalidad encaja, pero no debe usarse para justificar mezclar beta en la lista general.

### Regla de unsubscribe

Brevo documenta que, cuando se usan Consent Groups en formularios, puede sustituir el enlace estándar por `Update your preferences or Unsubscribe`.

Hay que probar cuidadosamente el comportamiento de:

- baja de un solo grupo;
- unsubscribe from all groups;
- global blocklist;
- comunicaciones no ligadas a grupos.

No asumir que “unsubscribe from all consent groups” equivale a global unsubscribe: Brevo documenta que son conceptos distintos.

---

## 5. Segmentos recomendados

### 5.1 Captación

- `SRC · Manecillas`
- `SRC · Fragmento`
- `SRC · Cuaderno`
- `SRC · Quiz Noveris`
- `SRC · Home/Explore/Popup`

Uso:

- entender calidad de captación;
- adaptar onboarding;
- comparar engagement sin crear listas redundantes.

### 5.2 Noveris

- `NOVERIS · Mensajero`
- `NOVERIS · Sabio`
- `NOVERIS · Silenciadora`
- `NOVERIS · Guardián`

Uso editorial:

- personalización ocasional;
- contenido de universo;
- no convertir el resultado lúdico en profiling serio.

### 5.3 Preferencias

Si `INTERESTS` existe o Consent Groups están disponibles:

- interés Manecillas;
- interés Samuel/Noveris;
- interés Cuaderno/recursos;
- interés eventos.

### 5.4 Engagement

Solo cuando la política de tracking permita usar esos datos de forma apropiada:

- engagement reciente 30/90 días;
- sin engagement 90/180 días;
- clickers de un tema concreto;
- nuevos suscriptores;
- nunca recibieron campaña;
- reactivación.

Si se usa tracking anónimo, los segmentos individualizados basados en apertura/clic pueden no estar disponibles o no ser apropiados. Diseñar la segmentación para degradar correctamente.

### 5.5 Lifecycle

- nuevos confirmados últimos 7 días;
- onboarding en progreso;
- onboarding completado;
- reengagement candidate;
- beta activo;
- beta proyecto cerrado/archivado.

### 5.6 CRM profesional

No modelar prensa como segmentación de newsletter. Para campañas operativas puntuales puede filtrarse CRM por:

- tipo de oportunidad;
- ciudad;
- etapa;
- relación;
- próximo follow-up;
- evento/libro asociado.

---

## 6. Taxonomía de lifecycle

### Estado 0 — visitante anónimo

No existe en Reader CRM.

Mantenerlo así mientras no se instale Tracker.

### Estado 1 — solicitud de alta pendiente DOI

El Worker devuelve `pending_confirmation`.

No mostrar como “suscrito” antes de que Brevo confirme el DOI.

### Estado 2 — suscriptor confirmado

Puede entrar en welcome journey.

### Estado 3 — lector con preferencias

Ha elegido uno o varios temas.

### Estado 4 — lector activo

Interactúa con campañas/contenido según la señal que se haya decidido medir.

### Estado 5 — inactivo

Definir solo tras acumular historial suficiente. No clasificar como inactivo a quien apenas ha tenido oportunidad de recibir emails.

### Estado 6 — reactivación

Un único intento o secuencia breve, no acoso.

### Estado 7 — baja/blocklist

No reactivar de forma automática.

Conservar el estado para evitar reimportarlo y reenviarle accidentalmente.

---

## 7. Métricas Reader CRM

No medir éxito solo por tamaño de lista.

### Adquisición

- altas iniciadas;
- DOI confirmados;
- ratio de confirmación DOI;
- fuente;
- crecimiento neto;
- bajas;
- bounces.

### Salud

- quejas;
- hard bounce;
- soft bounce persistente;
- blocklist;
- inactivos;
- dominios de destino principales;
- entregados.

### Engagement

Dependiendo de política de tracking:

- clicks;
- respuestas;
- conversion events;
- visitas atribuibles por UTM/analytics propios;
- preferencias modificadas;
- reuniones reservadas;
- descargas/acciones explícitas.

No usar opens como KPI primario: además de cuestiones de privacidad, los clientes de correo/proxies pueden degradar su fiabilidad.

### Negocio/editorial

- clics a retailer verificado, etiquetados como **retailer click**, no purchase;
- reservas de reuniones;
- invitaciones/eventos confirmados;
- lectores beta que completan feedback;
- crecimiento de audiencia de contenido;
- respuestas cualitativas.

---

## 8. De la fuente a la experiencia

### `home`

Welcome general.

### `popup`

Welcome general. No asumir interés específico por el contenido que estaba viendo salvo que `source` se extienda de forma segura y explícita.

### `explore`

Welcome general + mapa de la web.

### `manecillas`

Welcome con contexto de la obra, fragmento y novedades. Después del lanzamiento, compra solo si existe URL verificada.

### `fragmento`

Welcome de lectura: agradecer, enlazar siguiente acción relevante, evitar secuencia comercial agresiva.

### `cuaderno`

Welcome de contenido: otros artículos/recursos y opción de preferencias.

### `quiz`

Personalización ligera por `NOVERIS`; nunca enviar cuatro journeys enormes por un quiz con dos contactos.

### `lectores-beta`

Workflow separado: onboarding del programa, material, deadlines, feedback, cierre. No newsletter general por defecto.

---

## 9. Preferencias vs. inferencias

Orden de confianza:

1. **Consentimiento explícito**.
2. **Preferencia elegida**.
3. **Source de alta**.
4. **Acción explícita** — descarga, meeting, click— si la medición es legítima.
5. **Comportamiento inferido**.

Cuanto más abajo, menos debe determinar automáticamente qué recibe una persona.

---

## 10. Retención y minimización

Definir en política operativa:

- cuánto conservar contactos nunca confirmados si Brevo los guarda;
- cuánto conservar CRM profesional inactivo;
- blocklisted/unsubscribed se conservan cuando sea necesario para respetar la baja y evitar reimportación;
- no guardar eventos sin límite por comodidad;
- revisar atributos sin uso y eliminarlos tras migración segura.

Las decisiones finales de retención deben alinearse con la política de privacidad y asesoramiento legal cuando proceda.

---

## 11. Naming conventions

### Listas

`PURPOSE · Nombre`

Ejemplo:

- `PURPOSE · Lectores web`
- `PURPOSE · Lectores beta`

Si mantener los nombres actuales evita ruido, no renombrar por estética; documentar equivalencia.

### Segmentos

`DIM · Valor · ventana`

Ejemplos:

- `SRC · Manecillas`
- `ENG · Click 90d`
- `PREF · Cuaderno`
- `NOVERIS · Guardián`

### Campañas

`YYYY-MM-DD · OBJETIVO · AUDIENCIA · TEMA`

Ejemplo:

`2026-09-03 · LAUNCH · Lectores web · Manecillas`

El nombre interno puede ser sistemático; el subject visible sigue siendo editorial.

### Templates

`TYPE · PURPOSE · vN`

- `DOI · General · v2`
- `WELCOME · General · v1`
- `WELCOME · Manecillas · v1`
- `BETA · Onboarding · v1`

---

## 12. Señales de que estamos sobresegmentando

- segmentos con 0–2 personas durante meses;
- decenas de listas con el mismo consentimiento;
- journeys duplicados que solo cambian una frase;
- contenido editorial fragmentado hasta impedir campañas coherentes;
- automatizaciones difíciles de auditar;
- contactos que reciben más emails por estar en más grupos.

Cuando ocurra, simplificar.

---

## 13. DoD de Reader CRM

- [ ] Lista general verificada.
- [ ] Lista beta verificada y separada.
- [ ] `SOURCE` y `NOVERIS` documentados.
- [ ] No hay listas redundantes por source.
- [ ] Segmentos base definidos.
- [ ] Consent Groups evaluados.
- [ ] Preference center disponible si se usan preferencias.
- [ ] Lifecycle documentado.
- [ ] Welcome journeys probados.
- [ ] Tracking policy determinada.
- [ ] CRM profesional separado de marketing.
- [ ] Naming conventions aplicadas.
- [ ] Métricas no confunden retailer click con venta.
