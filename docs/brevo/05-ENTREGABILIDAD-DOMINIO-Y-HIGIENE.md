# 05 — Entregabilidad, dominio e higiene

**Objetivo:** que llegar a inbox sea una disciplina operativa, no una reacción cuando una campaña falla.

---

## 1. Prioridades de entregabilidad

Orden:

1. consentimiento y calidad de lista;
2. dominio autenticado;
3. remitente coherente;
4. contenido esperado;
5. bajas fáciles;
6. bounces/complaints controlados;
7. frecuencia consistente con la promesa;
8. IP adecuada al volumen;
9. observabilidad;
10. re-engagement/higiene.

Una IP dedicada no arregla una lista mala, un dominio sin autenticar o contenido no deseado.

---

## 2. Autenticación del dominio

Brevo documenta autenticación mediante:

- Brevo code/verification;
- DKIM;
- DMARC.

En 2026 está desplegando gradualmente un nuevo flujo unificado de configuración de dominio.

### Acción P0

Abrir `Settings/Domains` en la cuenta y registrar:

- dominio;
- status de verificación;
- DKIM;
- DMARC;
- sender domain;
- fecha de revisión;
- nuevo vs. antiguo flujo UI.

### No tocar DNS a ciegas

Antes de añadir/modificar:

- leer registros actuales del dominio;
- evitar duplicar DMARC;
- conocer proveedor DNS;
- revisar TTL;
- guardar diff;
- comprobar después con Brevo y herramientas DNS.

### DMARC

No elevar política a `quarantine`/`reject` como gesto SEO/seguridad sin comprobar todos los emisores legítimos del dominio.

Si Gmail u otros servicios también envían desde el dominio, validar alineación completa.

---

## 3. From / Reply-To

### From

Debe ser reconocible y estable.

Ejemplos conceptuales:

- `David Porto Díaz`
- `David Porto Díaz · Escritor`

Evitar rotaciones de nombres para “subir opens”.

### Reply-To

Usar una bandeja real monitorizada.

Para un autor, permitir respuesta directa puede mejorar relación y detectar problemas que ninguna métrica revela.

### Dirección de envío

Si actualmente se envía desde una dirección gratuita o un dominio no autenticable, evaluar una dirección bajo dominio propio. No inventar una nueva cuenta en esta PR.

---

## 4. Branded tracking subdomain

El nuevo flujo de dominio de Brevo puede incluir subdominio de tracking con marca.

Beneficios:

- URLs de tracking con dominio de marca;
- alineación/branding;
- potencial mejora de configuración en escenarios de IP dedicada.

### Gate

No activar automáticamente si hemos decidido usar tracking anónimo o mínimo.

El tracking subdomain es una capa distinta de la autenticación básica y debe alinearse con la política de seguimiento.

---

## 5. IP compartida vs. dedicada

Brevo recomienda IP dedicada cuando hay volumen alto y consistente, por ejemplo:

- al menos 3 campañas/semana a 3.000+ contactos;
- o >100.000 emails/mes.

También indica que, si no se mantiene ese volumen, es mejor una IP compartida.

### Situación de este proyecto

Último snapshot conocido: 2 suscriptores en lista canónica el 20/08/2026.

Conclusión:

**IP compartida.**

No comprar una IP dedicada en esta etapa.

### Coste actual documentado por Brevo

Add-on de IP dedicada: 251 €/año, disponible en Professional/Enterprise; Enterprise incluye una.

### Gate futuro

Reconsiderar solo si:

- volumen supera los umbrales de Brevo;
- frecuencia es estable;
- lista es sana;
- equipo puede gestionar warm-up/reputación;
- existe necesidad real de aislar reputación.

---

## 6. Warm-up

### IP compartida

No hacer “warm-up de IP dedicada”.

Aun así, una lista que crece rápido debe aumentar volumen con prudencia.

### IP dedicada futura

Brevo recomienda en las primeras semanas envíos frecuentes y consistentes para construir reputación. No comprar la IP hasta poder sostener ese patrón.

---

## 7. Bounces

### Hard bounce

Brevo bloquea automáticamente direcciones que producen hard bounce.

Acciones:

- no reintentar;
- no desbloquear automáticamente;
- investigar si una fuente genera tasas anormales;
- no borrar el estado por higiene cosmética.

### Soft bounce

Fallo temporal.

Observar tendencias:

- mailbox full;
- reputación;
- rate limiting del ISP;
- tamaño/contenido;
- incidencias temporales.

Escalar si se repite.

### Métricas

No fijar un único threshold universal en código sin contexto, pero tratar aumentos bruscos como incidente.

Brevo advierte que tasas altas de bounce pueden provocar suspensión para proteger reputación.

---

## 8. Complaints / spam

Cualquier complaint es una señal fuerte.

Proceso:

1. revisar campaña;
2. source del contacto si es posible;
3. consentimiento;
4. frecuencia;
5. subject/identidad;
6. baja;
7. si existe patrón, pausar envíos similares;
8. nunca reimportar quejas.

---

## 9. Unsubscribe

Una baja fácil protege:

- usuario;
- reputación;
- calidad de lista.

No ocultar enlace ni añadir pasos innecesarios.

### Preferencias

Preferencia parcial puede evitar una baja total, pero no convertir el preference center en una trampa.

Debe existir siempre salida total clara.

---

## 10. Higiene de lista

Brevo recomienda segmentar y gestionar inactivos; una práctica útil es excluir de campañas habituales contactos sin engagement durante 3–6 meses y tratarlos con reactivación, ajustando la ventana a la frecuencia real.

### Para nuestra baja frecuencia

No aplicar `90 días = inactivo` de forma mecánica si en esos 90 días solo hubo un email.

Definir inactividad por **oportunidades de engagement**, no solo por calendario.

Ejemplo futuro:

- recibió al menos 4 comunicaciones relevantes;
- no hizo ninguna acción observable;
- no tiene otra señal reciente;
- entonces entra en segmento reengagement.

### Bloquear vs. borrar

Preferir mantener estado de baja/blocklist para no reimportar accidentalmente.

Eliminar PII cuando proceda por política/solicitud, pero no como “optimización de open rate”.

---

## 11. Adquisición y calidad

Nunca:

- comprar listas;
- scrape emails;
- importar asistentes de eventos sin consentimiento adecuado;
- añadir contactos de Gmail por haber hablado con ellos;
- meter prensa en newsletter;
- usar concursos para obligar a newsletter si no está claramente consentido.

Sí:

- DOI;
- source attribution;
- formularios claros;
- valor específico;
- preference center.

---

## 12. Entregabilidad por source

Crear análisis futuro:

| Source | altas | DOI | entregados | hard bounce | baja | complaint | clicks |
|---|---:|---:|---:|---:|---:|---:|---:|

Objetivo: detectar formularios o campañas de captación con mala calidad.

No juzgar un source con 1–2 contactos.

---

## 13. Frecuencia y presión

Más emails no significan mejor entregabilidad.

Para el posicionamiento actual:

- frecuencia editorial moderada;
- no newsletter por obligación;
- evitar campaña + automation + evento el mismo día al mismo contacto;
- usar exclusiones/esperas.

Professional ofrece marketing pressure avanzado; no hace falta a esta escala.

---

## 14. Content deliverability QA

Antes de envío:

- subject no engañoso;
- From reconocible;
- reply-to válido;
- HTML limpio;
- text alternative;
- imágenes optimizadas;
- no attachment pesado salvo necesidad;
- enlaces HTTPS válidos;
- sin shorteners sospechosos;
- dominio autenticado;
- footer legal;
- unsubscribe;
- tracking conforme a política;
- no exceso de mayúsculas/urgencia artificial.

---

## 15. Monitoring

### Diario cuando haya campañas activas

- errores;
- bounces;
- complaints;
- blocklist changes;
- webhook failures.

### Tras cada campaña

24h y ventana final:

- delivery;
- bounce;
- complaint;
- unsubscribe;
- clicks/conversion;
- respuestas.

### Mensual

- tendencia de dominio;
- lista limpia;
- fuentes;
- inactivos;
- crecimiento neto;
- estado de autenticación.

### Trimestral

- DNS/auth;
- sender/reply-to;
- API/webhooks;
- IP strategy;
- automation overlap;
- política de tracking.

---

## 16. Webhooks de entregabilidad

Recomendado futuro:

Suscribirse como mínimo a eventos relevantes:

- delivered;
- hardBounce;
- softBounce;
- complaint/spam;
- unsubscribed;
- blocked;
- error;
- deferred si aporta valor.

No almacenar bodies completos indefinidamente.

Crear agregados y alertas.

---

## 17. Playbook: subida brusca de hard bounces

1. Pausar siguiente campaña similar.
2. Confirmar si problema es una fuente/lista concreta.
3. Revisar importaciones recientes.
4. Revisar dominio/remitente.
5. Leer mensajes de bounce.
6. No desbloquear.
7. Contactar soporte si Brevo suspende o hay anomalía de infraestructura.
8. Registrar causa/corrección.

---

## 18. Playbook: caída de entregabilidad

1. ¿Cambió dominio/DNS?
2. ¿Cambió From?
3. ¿Cambió IP/plan?
4. ¿Lista nueva/importada?
5. ¿Aumentó volumen?
6. ¿Aumentaron quejas/bounces?
7. ¿Cambió contenido/frecuencia?
8. ¿Incidencia Brevo/ISP?
9. ¿Problema solo en Gmail/Outlook/Yahoo?
10. Corregir causa, no “comprar IP dedicada” como respuesta automática.

---

## 19. Playbook: account suspension

- detener automatizaciones/campañas que puedan empeorar;
- leer causa exacta en Brevo;
- conservar evidencias;
- revisar fuentes/importaciones/bounces/complaints;
- no intentar sortear suspensión con otra cuenta;
- seguir procedimiento oficial de Brevo;
- documentar RCA.

---

## 20. DoD entregabilidad

- [ ] dominio autenticado;
- [ ] DKIM OK;
- [ ] DMARC revisado;
- [ ] From estable;
- [ ] Reply-To real;
- [ ] shared IP confirmada como estrategia;
- [ ] no dedicated IP sin volumen;
- [ ] bounces monitorizados;
- [ ] complaints monitorizadas;
- [ ] baja clara;
- [ ] hygiene segment definido cuando haya escala;
- [ ] webhook plan definido;
- [ ] playbooks disponibles;
- [ ] no imports sin provenance/consent.
