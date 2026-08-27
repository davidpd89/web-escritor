# 08 — Planes, costes, escalado y funcionalidades no aplicables

**Corte:** 2026-08-27  
**Objetivo:** decidir el plan por necesidades reales, no por checklist de funciones.

---

## 1. Regla financiera

Una funcionalidad de Brevo solo justifica gasto si:

1. resuelve un problema actual;
2. tiene una audiencia suficiente;
3. su coste es menor que el valor/tiempo que ahorra;
4. no puede resolverse razonablemente con el plan actual;
5. conocemos el coste total —plan + add-ons + canal—;
6. se puede medir su uso.

No subir de plan para «tenerlo todo».

---

## 2. Plan Gratis

Precio oficial ES a fecha de corte: **0 €/mes**.

Brevo documenta actualmente, entre otras capacidades:

- 300 emails/día;
- hasta 100.000 contactos almacenados;
- 1 usuario;
- campañas email/SMS;
- email/SMS transaccional;
- drag & drop editor;
- templates;
- secciones reutilizables;
- reporting básico;
- automation multicanal hasta 2.000 contactos únicos;
- herramientas gratuitas de ventas;
- Aura;
- outbound webhooks;
- soporte por email.

### Encaje actual

Muy alto mientras:

- lista siga pequeña;
- no necesitemos enviar >300 emails un día;
- no necesitemos A/B;
- no necesitemos unlimited automation contacts;
- reporting básico sea suficiente.

### Gate para salir de Free

- campaña legítima >300 destinatarios en un día;
- necesidad recurrente de más volumen;
- requerimiento Standard con ROI claro;
- 2.000 contactos únicos en automation cerca del límite.

---

## 3. Starter

Precio oficial ES: desde **7 €/mes**.

Tier inicial documentado:

- 5.000 emails/mes;
- hasta 500 contactos almacenados en ese tier;
- sin límite diario de envío;
- web push hasta 1.000 targeted subscribers/campaign;
- global data feeds;
- 1 conversion metric;
- remove Brevo logo como add-on;
- Sales Essentials como add-on.

### Limitación importante

Starter sigue teniendo el límite de **2.000 contactos únicos** en automatizaciones activas.

### Cuándo tiene sentido

- superar 300 emails/día ocasionalmente;
- 5.000 emails/mes son suficientes;
- no necesitamos A/B/send-time advanced;
- queremos una función Starter específica.

### Cuándo NO

Si el motivo real del upgrade es automation ilimitada o reporting avanzado, saltar la comparación hacia Standard.

---

## 4. Standard

Precio oficial ES: desde **17 €/mes**.

Funciones destacadas documentadas:

- 1 landing page;
- automation contacts ilimitados;
- A/B testing;
- optimización de hora de envío con IA;
- reporting/analytics avanzado;
- web push hasta 10.000 targeted subscribers/campaign;
- más opciones de usuarios como add-on;
- prioridad de soporte.

### Recomendación estratégica

**Probable sweet spot futuro** cuando exista una lista con tamaño y cadencia suficientes.

No necesariamente ahora.

### Gates concretos

Subir a Standard si se cumple al menos uno y tiene uso inmediato:

- automation >2.000 contactos;
- A/B con muestras suficientemente grandes;
- send-time optimization aporta valor y política de tracking lo permite;
- reporting avanzado se usa mensualmente;
- landing page temporal resuelve un flujo real;
- el coste mensual es trivial frente al valor operativo.

---

## 5. Professional

Precio oficial ES: desde **499 €/mes**.

Capacidades documentadas incluyen:

- 150k–10M emails/mes;
- hasta 2M contactos;
- 10 seats;
- custom data feeds;
- synchronized reusable sections;
- AI product recommendations;
- back-in-stock;
- WhatsApp campaigns/transactional;
- web/mobile push hasta 20k targeted subscribers/campaign;
- marketing pressure;
- 1 custom object;
- AI segmentation;
- 10 landing pages;
- analytics studio;
- contact scoring;
- incoming webhooks;
- dedicated IP add-on;
- Sales Advanced add-on;
- soporte avanzado y horas de especialistas según condiciones del plan.

### Decisión actual

**NO JUSTIFICADO.**

La escala conocida del proyecto no se aproxima al caso de uso de Professional.

### No comprar Professional por una única curiosidad

No justificar 499 €/mes solo para:

- WhatsApp;
- contact scoring;
- AI segmentation;
- marketing pressure;
- 10 landing pages;
- dashboard más bonito;
- mobile push que no podemos usar sin app.

### Gate futuro

Reabrir solo si varias funciones Professional se convierten simultáneamente en necesidades operativas con volumen/ROI demostrable.

---

## 6. Enterprise

Precio: personalizado.

Incluye/puede incluir:

- contactos ilimitados;
- sub-organizations;
- mayor push;
- Wallet;
- loyalty add-on;
- custom objects;
- data transformation;
- data warehouse/SFTP;
- IP dedicada incluida;
- SAML SSO;
- SLA;
- customer success.

### Estado

`NOT APPLICABLE` para la etapa actual.

No evaluar salvo cambio radical de escala/organización.

---

## 7. IP dedicada

Coste oficial actual: **251 €/año** como add-on, Professional/Enterprise; Enterprise incluye una.

Brevo recomienda IP dedicada si se mantienen volúmenes como:

- 3+ campañas/semana a 3.000+ contactos;
- o >100.000 emails/mes.

### Estado

`NO COMPRAR`.

La lista históricamente verificada tenía 2 contactos; incluso con crecimiento fuerte estamos muy lejos de esos umbrales.

Una IP dedicada infrautilizada puede ser peor porque no mantiene reputación consistente.

---

## 8. Email credits prepago

Disponibles en todos los planes.

Brevo indica:

- paquetes de emails;
- no caducan;
- pueden servir para envíos ocasionales/extra;
- activan determinadas capacidades asociadas a Starter según condiciones vigentes.

### Uso potencial

Si seguimos enviando muy ocasionalmente y necesitamos un pico que Free no cubra, comparar créditos prepago vs. Starter mensual.

No comprar preventivamente.

---

## 9. SMS credits

- disponibles como add-on en todos los planes;
- packs desde 100;
- no caducan;
- coste depende de país y longitud.

### Estado

`DEFER` hasta existir captura de teléfono + consentimiento + caso de uso.

---

## 10. WhatsApp credits

- add-on Professional/Enterprise;
- coste según país y tipo de template;
- no caducan.

### Estado

`DEFER / NO UPGRADE FOR THIS ALONE`.

---

## 11. Sales add-ons

Todos los planes ya incluyen ventas gratuitas con límites.

Antes de comprar Sales Essentials/Advanced:

1. usar pipeline gratuito;
2. medir si 50 deals abiertos / 1 pipeline se quedan cortos;
3. usar Meetings/Tasks/1 mailbox;
4. identificar limitación real;
5. solo entonces comparar add-on.

---

## 12. SAML SSO

Professional add-on / incluido Enterprise según pricing.

No hay equipo empresarial que lo justifique ahora.

`N/A`.

2FA + cuenta controlada + usuarios mínimos es suficiente en esta etapa.

---

## 13. Landing pages

### Free/Starter

No basar estrategia en landing page Brevo si no está incluida.

### Standard

1 landing page.

### Professional

10.

### Decisión

No subir de plan por landing pages: tenemos un sitio propio con mejor control de SEO/UX.

---

## 14. Web Push

### Starter

Hasta 1.000 targeted subscribers/campaign según pricing actual.

### Standard

Hasta 10.000.

### Professional

Hasta 20.000.

### Enterprise

Hasta 40.000.

### Decisión

No es criterio de upgrade ahora. Primero demostrar audiencia recurrente + consentimiento + caso de uso.

---

## 15. Mobile Push

No hay app móvil.

`N/A`.

---

## 16. Ecommerce features

Professional incluye capacidades como product recommendations/back-in-stock.

Sin ecommerce directo observable:

`N/A`.

No subir plan para imitar una tienda que no somos.

---

## 17. Custom Objects

Professional/Enterprise.

Para nuestro modelo:

- libros, artículos y recursos ya viven en el repo/site;
- oportunidades caben en Deals;
- contactos en Contacts;
- compañías en Companies.

No crear custom object “Book” solo porque existe la función.

Gate: necesidad relacional compleja que no quepa en modelo estándar.

---

## 18. Contact scoring

Professional.

Con lista pequeña:

- ruido;
- falsa precisión;
- coste injustificado.

Usar segmentos simples antes.

Gate: miles de contactos + equipo tomando decisiones distintas según score + datos suficientes.

---

## 19. AI segmentation

Professional.

No necesaria mientras las preguntas sean simples:

- source;
- preferencias;
- engagement;
- lifecycle.

Los segmentos explícitos son más auditables.

---

## 20. Marketing pressure

Professional.

No necesaria si enviamos poco.

Si empiezan a coexistir muchas campañas/automations, primero resolver con calendarios, exclusiones y segmentos.

---

## 21. Incoming webhooks

Professional según pricing actual.

No confundir con **outbound webhooks** desde Brevo, disponibles en capacidades inferiores/API.

Para nuestra observabilidad necesitamos principalmente recibir eventos salientes de Brevo en nuestro endpoint; no hace falta Professional solo por “webhooks”.

---

## 22. Conversations / chat

No subir plan por chat si ya existe asistente y no hay equipo de soporte.

Inbox multicanal se evalúa por ahorro real de trabajo.

---

## 23. Cost model recomendado

### Etapa A — microaudiencia

Plan objetivo: **Free**, salvo que la cuenta actual ya sea otra y exista razón para mantenerla.

Coste adicional objetivo: 0 €.

### Etapa B — cientos de contactos / lanzamiento activo

Comparar:

- Free + créditos puntuales;
- Starter;
- Standard.

Decidir según volumen diario, automation y reporting.

### Etapa C — >2.000 contactos en automation / newsletter madura

Standard probablemente tiene sentido.

### Etapa D — operación multicanal grande

Professional solo con volumen/ROI.

### Etapa E — organización/ecommerce/loyalty a escala

Enterprise si el proyecto ha cambiado radicalmente.

---

## 24. Matriz de decisiones

| Necesidad | Solución mínima | ¿Upgrade? |
|---|---|---|
| 2–100 suscriptores | Free | No |
| >300 emails en un día, ocasional | créditos/Starter | Evaluar |
| >300 emails/día frecuente | Starter+ | Sí |
| >2.000 contactos en automation | Standard | Sí |
| A/B útil | Standard | Sí cuando haya muestra |
| send-time IA | Standard | Solo si aporta |
| advanced reports | Standard | Si se usan |
| 1 landing temporal | Standard | No por sí sola |
| WhatsApp marketing | Professional | No ahora |
| scoring | Professional | No ahora |
| dedicated IP | Pro/Enterprise + add-on | No hasta volumen alto |
| CRM básico | Incluido | No |
| Meetings básico | Incluido | No |
| SMS puntual | créditos | No plan por sí solo |
| Web push | Starter+ | Defer |
| Mobile push | Pro+ | N/A |
| Loyalty/Wallet | Enterprise | N/A |

---

## 25. Anti-patrones de coste

- upgrade porque “el logo de Brevo queda feo” sin valorar add-on/tier;
- pagar Standard antes de tener audiencia para A/B;
- pagar Pro para WhatsApp sin teléfonos;
- IP dedicada con 200 contactos;
- pagar landing pages teniendo GitHub/site propio;
- comprar SMS credits antes de captar consentimiento SMS;
- acumular add-ons que superan el valor de la herramienta;
- elegir plan anual sin validar uso real;
- mantener plan superior tras terminar un periodo de lanzamiento sin revisar.

---

## 26. Revisión de plan trimestral

Registrar:

- plan actual;
- coste;
- emails enviados/mes;
- contactos almacenados;
- contactos automation;
- features premium usadas realmente;
- features premium sin uso;
- add-ons;
- próximo gate.

Pregunta final:

**Si bajásemos un plan hoy, ¿qué proceso real dejaría de funcionar?**

Si la respuesta es “ninguno”, revisar downgrade.

---

## 27. DoD de costes

- [ ] plan actual verificado live;
- [ ] coste mensual/anual conocido;
- [ ] add-ons inventariados;
- [ ] no dedicated IP;
- [ ] Professional descartado mientras no haya ROI;
- [ ] Standard tiene gates claros;
- [ ] créditos solo bajo necesidad;
- [ ] review trimestral programada operativamente;
- [ ] cada upgrade tiene una feature/volumen que lo justifica.
