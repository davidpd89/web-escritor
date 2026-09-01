# H.6 · CTA de reenvío/compartir en newsletter

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Matriz:** `PILOTAR BAJO COSTE`  
**Decisión:** un CTA sencillo de compartir puede pilotarse cuando exista una hipótesis de crecimiento medible y un template estable; no construir un programa de referrals por defecto.  
**Naturaleza:** documentación; no modifica emails ni Brevo.

## 1. Hipótesis original

Añadir en cada email una invitación tipo “reenvía esto a alguien a quien le gustaría” y un enlace claro a la suscripción para favorecer crecimiento orgánico boca-oreja.

## 2. Evolución

La revisión lo dejó `CONDITIONAL`: bajo coste potencial, pero sin asumir que un botón produce crecimiento. La matriz lo formuló como `PILOTAR BAJO COSTE`; autoridad final y JSON mantuvieron `CONDITIONAL`.

## 3. Condiciones previas

Antes del piloto deben estar estables:

- template base de email;
- DOI y alta correctos;
- URL canónica de suscripción;
- copy/propósito de newsletter;
- medición UTM/referral suficientemente simple;
- privacidad y baja sin fricciones.

H.6 no debe competir con H.1/H.2 mientras el journey base siga sin verificación E2E completa.

## 4. Implementación mínima futura

Preferir un bloque editorial simple:

- texto humano de reenvío/compartir;
- enlace público de suscripción, no datos del destinatario;
- UTM/referrer opcional y no identificable si hace falta atribución;
- fallback que siga funcionando si el cliente de correo bloquea estilos/imágenes.

No hace falta cuenta, código de invitación personal, recompensa, leaderboard ni backend nuevo.

## 5. Medición

Hipótesis ejemplo: “un CTA visible de reenvío genera nuevas visitas/suscripciones atribuibles sin aumentar bajas”.

Medir, de forma agregada:

- clics al enlace de suscripción desde email compartido;
- altas confirmadas atribuibles si el modelo actual permite hacerlo sin perfilado invasivo;
- bajas/quejas como guardrail.

No afirmar crecimiento por el número de clics si no se observa la conversión posterior.

## 6. Riesgos

- reenviar puede exponer contenido personalizado si el email contiene datos del destinatario;
- query params pueden filtrar identificadores si se diseñan mal;
- un sistema de referrals sobredimensionado crea tracking y deuda;
- copy insistente puede degradar la voz editorial;
- incentivo/recompensa cambia naturaleza comercial y requiere otro análisis.

## 7. Qué no hacer

- No meter email/id del suscriptor en la URL pública de compartir.
- No crear referral codes individuales sin necesidad.
- No añadir otro SaaS de referral.
- No ofrecer premios ficticios.
- No convertir cada campaña en una petición insistente de difusión.
- No confundir “forward” del cliente de correo con consentimiento del receptor reenviado.

## 8. Definition of Done si se pilote

- [ ] template estable;
- [ ] URL pública segura;
- [ ] cero PII en parámetros;
- [ ] hipótesis/métrica definida;
- [ ] CTA funciona en clientes principales y plain text;
- [ ] medición agregada suficiente;
- [ ] revisión posterior KEEP/CHANGE/STOP.

## 9. Trazabilidad #135

Banco original; revisión (`CONDITIONAL`); matriz (`PILOTAR BAJO COSTE`); `docs/brevo/04` y taxonomía UTM; JSON/autoridad final; revalidación independiente. Sin evidencia posterior que lo convierta en obligación.

## 10. Cierre

H.6 puede ser un experimento pequeño cuando el email base ya funciona. El valor está en reducir fricción para compartir, no en construir otra plataforma de referrals.