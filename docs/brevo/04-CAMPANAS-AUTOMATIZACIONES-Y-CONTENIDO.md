# 04 — Campañas, automatizaciones y contenido

**Objetivo:** definir qué automatizar, qué enviar, cómo medirlo y qué debe seguir siendo una decisión editorial humana.

---

## 1. Regla editorial

Brevo automatiza:

- triggers;
- esperas;
- segmentación;
- condiciones;
- envíos;
- registro;
- exclusiones;
- recordatorios.

Brevo **no debe decidir por sí solo**:

- hechos sobre libros;
- disponibilidad comercial;
- premios;
- voz de autor;
- claims;
- frecuencia editorial;
- cambios de estrategia.

El copy final se revisa antes de activar una automatización/campaña.

---

## 2. Inventario de journeys objetivo

### J1 — DOI

Trigger: petición de alta.

Objetivo: confirmar consentimiento.

No es un email de bienvenida ni promocional.

### J2 — Welcome general

Trigger: alta confirmada en `Lectores web`.

Objetivo:

- dar contexto;
- explicar qué recibirá;
- ofrecer una primera acción útil;
- permitir preferencias.

Propuesta compacta:

1. bienvenida inmediata;
2. opcionalmente, segundo email varios días después si existe contenido realmente útil.

No crear una secuencia de 7 emails por defecto.

### J3 — Welcome Manecillas

Trigger posible:

- `SOURCE = manecillas` o interés explícito.

Contenido:

- contexto de la obra;
- fragmento;
- guía/recursos si existen;
- novedades verificadas.

Regla comercial:

- no afirmar “ya disponible” antes de la fecha/estado real;
- no atribuir retailer sin URL verificada;
- no modelar PVP como oferta propia.

### J4 — Fragmento

Trigger: `SOURCE = fragmento`.

Objetivo:

- cerrar la experiencia de lectura;
- enlazar la página del libro;
- dar opción de elegir preferencias.

### J5 — Cuaderno

Trigger: `SOURCE = cuaderno`.

Objetivo:

- conectar con contenidos/recursos relacionados;
- no asumir que la persona quiere emails puramente promocionales de libros si el consentimiento no lo dice.

### J6 — Noveris

Trigger: `SOURCE = quiz-noveris`.

Condición: `NOVERIS`.

Personalización posible:

- bloque o párrafo diferente por resultado;
- recomendación de contenido del universo;
- no cuatro funnels completos hasta que haya volumen que lo justifique.

### J7 — Lectores beta

Trigger: alta confirmada en lista beta.

Flujo separado:

1. onboarding/programa y expectativas;
2. material cuando esté listo;
3. recordatorio razonable;
4. feedback;
5. agradecimiento/cierre;
6. archivo de proyecto.

Nunca añadir general newsletter sin otro opt-in.

### J8 — Re-engagement

Crear solo con suficiente historial.

Trigger: inactividad significativa definida por campaña/engagement legítimamente medible.

Flujo:

1. un email de reactivación útil;
2. opcional segundo recordatorio;
3. dejar de incluir en campañas frecuentes si no responde;
4. preservar estado/consentimiento según política.

No usar tácticas manipulativas tipo “te vamos a borrar en 24h” si no es verdad.

---

## 3. Automatizaciones — límites y plan

Brevo documenta actualmente:

- Free y Starter: hasta 2.000 contactos únicos en automatizaciones activas;
- Standard+: contactos ilimitados;
- Free/Starter/Standard: 6.000 eventos/min y 3.000 steps/min;
- Professional/Enterprise: límites mayores.

Para la escala conocida del proyecto, esos límites no justifican upgrade hoy.

### Gate de upgrade por automation

Subir a Standard cuando:

- el límite de 2.000 contactos únicos se acerque de forma real;
- o A/B + send-time + reporting avanzado aporten suficiente valor;
- o otro beneficio Standard tenga uso inmediato.

No pagar Standard “por si acaso”.

---

## 4. Auditoría de automatizaciones legacy

Para cada workflow existente, crear ficha:

```text
ID/nombre:
Estado:
Propósito:
Trigger:
Reentrada:
Audiencia:
Exclusiones:
Pasos:
Templates:
Delays:
Goals:
Tracking:
Último cambio:
Última ejecución:
Métricas:
Dependencias:
Riesgos:
Decisión: KEEP / REWRITE / PAUSE / ARCHIVE
```

### Plantillas `Bienvenida_Samuel_*`

Revisar especialmente:

- si siguen activas;
- si corresponden al posicionamiento actual;
- si prometen contenido/capítulo;
- si usan enlaces antiguos;
- si mezclan consentimiento;
- si una alta de Manecillas podría entrar accidentalmente;
- si templates duplicados pueden consolidarse.

---

## 5. Campaign taxonomy

### Nombre interno

`YYYY-MM-DD · TYPE · AUDIENCE · SUBJECT`

Types:

- `NEWS`
- `LAUNCH`
- `CONTENT`
- `EVENT`
- `BETA`
- `REENGAGE`
- `SERVICE` (solo cuando realmente sea servicio)

Ejemplos:

- `2026-09-03 · LAUNCH · Lectores web · Manecillas`
- `2026-09-15 · CONTENT · Cuaderno · Portal fantasy`

### Tags/UTM

Convención recomendada:

- `utm_source=brevo`
- `utm_medium=email`
- `utm_campaign=<slug-estable>`
- `utm_content=<bloque-o-cta>` cuando aporte análisis
- `utm_term` solo si existe un uso consistente.

Brevo permite activar UTM en campañas y en 2026 ha ampliado campos personalizables vía API.

No añadir UTM a URLs donde rompa una lógica específica; preservar canonicals.

---

## 6. Brand Library y templates

Configurar Brand Library con:

- logo correcto;
- colores de marca;
- tipografías compatibles con email;
- enlaces sociales canónicos;
- nombre/identidad del remitente.

### Sistema de templates

Mantener pocos templates base:

1. `BASE · Editorial`
2. `DOI · General`
3. `WELCOME · General`
4. `WELCOME · Manecillas`
5. `BETA · Base`
6. `EVENT · Base`

Usar secciones reutilizables para:

- cabecera;
- pie legal;
- bloque autor;
- CTA estándar;
- redes;
- preference/unsubscribe.

No crear una plantilla completa por campaña.

### Email design QA

Probar:

- Gmail web/mobile;
- Outlook;
- Apple Mail/iOS cuando sea posible;
- dark mode;
- images off;
- links;
- plain-text/fallback;
- tamaño táctil;
- accesibilidad;
- alt text;
- contraste;
- ancho;
- subject/preheader;
- pie de preferencias/baja.

---

## 7. Frecuencia

La política pública actual dice “sin boletines frecuentes”.

Por tanto, de momento:

- enviar cuando exista algo útil;
- evitar cadencia artificial semanal solo para “mantener engagement”;
- no superar expectativas del consentimiento.

### Frequency cap

Si el plan/función lo permite y aumenta la actividad:

- usar presión/frequency control para impedir solapamiento entre automatizaciones y campañas;
- especialmente importante si una persona pertenece a varios intereses.

Professional tiene funcionalidades de marketing pressure más avanzadas; no pagar por ellas mientras pueda resolverse con disciplina editorial y segmentos.

---

## 8. A/B testing

Standard incluye A/B testing.

Brevo permite probar:

- subject;
- contenido.

### Cuándo usar

Solo con audiencia suficiente para que las muestras aporten información.

Con decenas de contactos, un “ganador” puede ser ruido estadístico.

### Qué probar primero cuando haya escala

1. subject claro vs. curiosity moderada;
2. CTA;
3. estructura larga/corta;
4. enfoque editorial.

No probar múltiples variables simultáneamente en un test simple.

No optimizar clickbait que degrade confianza.

---

## 9. Send at best time / Aura AI

Standard incluye optimización de hora de envío con IA.

Brevo usa engagement previo y, para contactos sin historial, información agregada.

### Uso recomendado

- no usar en la primera campaña como supuesto mágico;
- acumular historial;
- activarlo en campañas no urgentes;
- no usar para eventos donde la hora de comunicación sea crítica;
- recordar que no está disponible en ciertas combinaciones, como A/B o tracking anónimo.

Si se adopta tracking anónimo por privacidad, aceptar que algunas optimizaciones individualizadas pueden dejar de estar disponibles.

---

## 10. Reporting

### Mínimo por campaña

- enviados;
- entregados;
- hard bounces;
- soft bounces;
- complaints;
- unsubscribes;
- clicks;
- conversion events;
- respuestas observables;
- UTM traffic.

### Standard+

Puede aportar reporting avanzado como heatmaps/geografía, según plan.

No reaccionar a una sola campaña con audiencia diminuta.

### Review template

```text
Campaña:
Objetivo:
Audiencia:
Tamaño:
Entregados:
Bounces:
Quejas:
Bajas:
Clicks:
Conversiones:
Top links:
Respuestas cualitativas:
Qué aprendemos:
Qué NO podemos concluir:
Acción siguiente:
```

---

## 11. Conversiones

Brevo permite definir métricas de conversión; el número disponible depende del plan.

### No llamar conversión a todo

Propuestas válidas:

- `fragment_downloaded`
- `beta_feedback_submitted`
- `meeting_booked`
- `resource_downloaded`
- `retailer_link_clicked`

### Retailer

`retailer_link_clicked` = clic saliente a tienda.

No significa:

- compra;
- ingreso;
- libro vendido.

No rellenar revenue ficticio.

### Si solo hay 1 conversion metric

Elegir la que mejor mida el objetivo del periodo, no cinco pseudoconversiones.

Para lanzamiento con retailer externo podría ser `retailer_link_clicked`; para construcción de audiencia quizá una acción editorial más relevante.

---

## 12. Campañas por etapa del proyecto

### Prelanzamiento Manecillas

- fragmento;
- contexto editorial;
- fecha oficial;
- eventos confirmados;
- no “compra ya” sin disponibilidad verificada.

### Lanzamiento

Solo tras verificar estado comercial:

- anuncio factual;
- CTA a retailer/sitio verificado;
- UTM;
- no atribuir disponibilidad universal.

### Postlanzamiento

- prensa/eventos;
- clubes de lectura;
- contenido relacionado;
- reseñas solo si verificadas y con permiso/contexto;
- no repetir emails de compra a toda la lista.

### Evergreen

- Cuaderno;
- herramientas;
- recursos;
- procesos de escritura;
- agenda relevante;
- nuevos proyectos.

---

## 13. Content blocks por preferencias

Una campaña puede ser única y tener bloques condicionales/segmentos, en lugar de duplicar campaña.

Ejemplo:

- cabecera común;
- bloque Manecillas solo interesados;
- bloque Cuaderno solo preferencia recursos;
- evento según segmento/geografía solo si dato legítimo y útil.

Evitar personalización “creepy”.

---

## 14. Reply-to y relación humana

Para un autor, las respuestas pueden valer más que un punto de CTR.

Configurar Reply-To real y monitorizado.

Animar a responder en campañas donde tenga sentido.

No usar `no-reply` salvo obligación técnica.

### Triage de respuestas

- lector: responder/guardar contexto mínimo;
- prensa/profesional: convertir en deal/task si procede;
- baja: respetar inmediatamente;
- abuso/spam: gestionar sin incorporar más datos.

---

## 15. Campañas que NO debemos crear ahora

- carrito abandonado: no hay ecommerce directo.
- back-in-stock: no gestionamos stock propio.
- loyalty: no hay programa.
- recomendaciones de producto IA: no hay catálogo ecommerce propio que lo justifique.
- SMS marketing: no recopilamos teléfono.
- WhatsApp marketing: coste/plan/consentimiento no justificados.
- push masivo: no hay caso de uso suficiente.
- birthday emails: no recopilamos cumpleaños.

---

## 16. Pre-send checklist

- [ ] Objetivo único.
- [ ] Audiencia correcta.
- [ ] Consentimiento/purpose correcto.
- [ ] Exclusiones correctas.
- [ ] Hechos verificados.
- [ ] Links verificados.
- [ ] UTM consistente.
- [ ] Subject y preheader.
- [ ] From/Reply-To.
- [ ] Baja/preferencias.
- [ ] Tracking conforme a política.
- [ ] Alt text.
- [ ] Mobile/dark mode.
- [ ] Test email.
- [ ] No PII en URLs.
- [ ] No retailer/compra inventado.
- [ ] No conflicto con otra automatización/campaña.

---

## 17. DoD campañas/automation

- [ ] Automatizaciones legacy auditadas.
- [ ] Welcome general probado.
- [ ] Manecillas journey definido y factual.
- [ ] Beta workflow separado.
- [ ] Naming/UTM aplicado.
- [ ] Templates consolidados.
- [ ] Brand Library configurada.
- [ ] Reporting review template adoptado.
- [ ] Conversion taxonomy adoptada.
- [ ] Re-engagement solo cuando haya datos suficientes.
- [ ] Ningún workflow manda emails por una lista equivocada.
