# J.1 · Hilos de discusión previos a clubes de lectura

**Estado histórico final de PR #135:** `DEFER`  
**Matriz intermedia:** `DEFERIR`  
**Regla:** no construir identidad, comentarios persistentes, moderación ni backend comunitario sin demanda/masa crítica demostradas.

## 1. Hipótesis original

J.1 proponía añadir hilos asíncronos previos a reuniones de club de lectura para generar anticipación y participación antes de la sesión en vivo.

La idea venía de patrones de comunidades lectoras, pero la revisión del proyecto mostró que trasladar ese patrón literalmente a davidportodiaz.com no era una “mejora de página”: implicaba operar una comunidad.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Hilos asíncronos antes de sesión del club. |
| Revisión 108/108 | `DEFER` | Identidad, moderación, spam/abuso y backend son desproporcionados hoy. |
| Matriz operativa | `DEFERIR` | Incluso Giscus sería mal encaje por exigir GitHub login a lectores generales. |
| Repo cross-check | alternativa | Preferir AMA, email, club real o plataformas existentes antes que foro propio. |
| Overrides | `DEFER` reafirmado | Masa crítica y privacidad no justificadas. |
| Autoridad final | `DEFER` | No abrir superficie comunitaria persistente ahora. |
| Revalidación independiente | mantenido | Evitar moderación/identidad sin demanda real. |

## 3. Estado real de `main` al 29/08/2026

El sitio ya tiene componentes comunitarios/editoriales sin convertirse en red social:

- `/clubes-de-lectura/samuel-entre-mundos/` ofrece guía oficial, preguntas de debate, guía imprimible e invitación al autor;
- `/lectores-beta/` declara explícitamente que el grupo es pequeño y la operación es manual;
- esa página también aclara que **no hay comunidad pública, perfiles ni foro**;
- la web dispone de email/newsletter y contacto como canales de relación;
- no se ha encontrado en las autoridades inspeccionadas un backend de cuentas/comentarios que deba “completarse”.

Eso es una decisión arquitectónica valiosa, no una carencia accidental.

## 4. Qué cambia realmente si se implementa un hilo propio

Aunque el UI parezca una lista de mensajes, hay que resolver:

- identidad o pseudónimo;
- autenticación/recuperación de cuenta si existe login;
- almacenamiento persistente;
- moderación;
- spam/bots;
- abuso/acoso;
- reportes;
- edición/borrado;
- retención;
- derechos RGPD;
- PII en mensajes;
- menores potenciales si el público incluye lectores juveniles;
- spoilers;
- notificaciones;
- rate limits;
- backups;
- disponibilidad del servicio;
- accesibilidad del flujo de composición/lectura.

Por eso J.1 no debe aparecer como “añadir comentarios”.

## 5. Por qué Giscus/Disqus equivalentes no resuelven automáticamente el problema

La matriz estudió específicamente la tentación de usar un tercero gratuito.

Un tercero puede reducir backend propio, pero introduce:

- cuenta/login externo;
- política de privacidad de otro proveedor;
- scripts/cookies/network adicionales;
- CSP;
- dependencia operacional;
- UX ajena a lectores no técnicos;
- moderación que sigue siendo responsabilidad editorial.

En particular, exigir una cuenta GitHub a un club de lectura general es una fricción artificial.

No instalar una plataforma de comentarios solo porque sea gratis.

## 6. Alternativas aprobadas antes de J.1

Para obtener conversación sin crear comunidad persistente:

1. preguntas para una sesión real recogidas por coordinador del club;
2. AMA asíncrono editorial (J.5) con preguntas moderadas y respuestas publicadas;
3. email/contacto cuando sea apropiado;
4. formularios temporales con finalidad clara, si se justifican;
5. conversación en la plataforma donde ya exista la comunidad del club;
6. publicación posterior de una selección editada/anónima con permiso.

Estas opciones conservan el valor humano sin abrir identidad/foro sitewide.

## 7. Trigger para reabrir J.1

No basta con “sería bonito tener comunidad”. Reabrir solo si existe evidencia como:

- varios clubes activos/recurrentes piden un espacio común;
- un volumen estable de preguntas/discusión que email/AMA ya no gestiona razonablemente;
- una persona/rol responsable de moderación;
- política de spoilers y conducta;
- decisión explícita sobre identidad/autenticación;
- recursos para incidentes/abuso;
- privacidad/retención definidas;
- beneficio medible que no resuelve una plataforma externa ya usada por el club.

## 8. Si algún día se reabre: decidir primero el modelo

Antes de elegir tecnología, especificar:

### Opción A — sin cuentas, moderación previa

Formulario → cola privada → publicación editorial aprobada.

Menos superficie, pero no es un “hilo” en tiempo real.

### Opción B — comunidad externa existente

El sitio enlaza/integra de forma mínima, sin replicar mensajes.

### Opción C — comunidad propia

Solo con business/product decision consciente de que se está creando un servicio con identidad y moderación.

La tecnología se elige después.

## 9. Privacidad y menores

Dado el contexto juvenil de parte del catálogo/club:

- no pedir edad/fecha de nacimiento salvo necesidad real;
- no publicar emails;
- no fomentar datos personales en mensajes;
- disponer de retirada/report;
- revisar implicaciones específicas si se permite participación de menores;
- no asumir que un simple checkbox resuelve toda la operación.

J.1 queda `DEFER` precisamente para no abrir esta superficie por inercia.

## 10. Relación con otras ideas

- **J.2:** guías por capítulo pueden ayudar a un club sin crear foro.
- **J.3:** calendario ICS cubre logística de sesión sin identidad.
- **J.5:** AMA editorial es la alternativa preferida para conversación pública propia.
- **J.6:** lectores beta ya funciona como grupo pequeño/manual con finalidad separada.
- **G.5/I.5:** preguntas/mensajes implican PII/retención si se almacenan.
- **K.1:** igual que venta directa, crear una operación real no debe disfrazarse de pequeño formulario.

## 11. Qué no hacer

- No añadir Disqus/Giscus por checklist.
- No crear login solo para comentarios.
- No usar GitHub Discussions como interfaz para lectores generales sin demanda.
- No guardar mensajes indefinidamente.
- No abrir comentarios anónimos sin moderación/antiabuso.
- No presentar un foro vacío como comunidad.
- No mezclar lectores beta con comunidad pública.
- No usar un hilo como excusa para recopilar perfiles/intereses.

## 12. Definition of Done para una futura reevaluación

- [ ] demanda recurrente demostrada;
- [ ] responsable de moderación;
- [ ] modelo de identidad definido;
- [ ] política de conducta/spoilers/reportes;
- [ ] PII/retención/borrado documentados;
- [ ] evaluación de menores cuando aplique;
- [ ] alternativa AMA/email/plataforma existente comparada;
- [ ] coste/beneficio documentado;
- [ ] accesibilidad/abuso/seguridad incluidos en DoD;
- [ ] no se crea una comunidad vacía por “engagement”.

## 13. Trazabilidad #135

Revisados:

- banco original J.1;
- revisión 108/108: `DEFER` por identidad/moderación/spam/backend;
- matriz final: `DEFERIR`, incluido mal encaje de Giscus/GitHub login;
- repo cross-check/overrides: preferir AMA/email/club/plataformas existentes;
- autoridad machine-readable;
- autoridad humana final: `DEFER`;
- revalidación independiente: estados J mantenidos y advertencia contra abrir identidad/moderación sin demanda.

## 14. Cierre

J.1 se difiere porque el coste real no son los mensajes sino **operar el sistema social que los hace seguros y mantenibles**. La web ya puede generar conversación mediante clubes, beta, email y AMA editorial sin asumir todavía esa carga.