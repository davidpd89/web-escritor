# J.4 · Insignias/reconocimiento de participación

**Estado histórico final de PR #135:** `REJECT`  
**Matriz intermedia:** `DESCARTAR`  
**Regla:** no crear badges, puntos ni estado artificial sin una comunidad/identidad estable y una conducta real que necesite incentivo.

## 1. Hipótesis original

J.4 proponía reconocimiento simbólico y discreto para lectores que completasen un club o una serie, evitando gamificación agresiva.

La formulación ya intentaba ser prudente, pero #135 concluyó que el problema no era el tono del badge: **el sitio no tenía un sistema de identidad/comunidad ni una necesidad demostrada que justificase crear estado persistente para premiar participación**.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Micro-gamificación/reconocimiento discreto. |
| Revisión 108/108 | `REJECT` | Sin identidad/comunidad estable, badges son ruido y estado artificial. |
| Matriz operativa | `DESCARTAR` | No resuelve una necesidad demostrada y puede degradar el tono editorial. |
| Repo cross-check | alternativa | Preferir reconocimiento editorial real cuando exista participación. |
| Autoridad final | `REJECT` | No debe volver al backlog como feature por defecto. |
| Revalidación independiente | mantenido | No abrir identidad/moderación sin demanda. |

No convertir `REJECT` en `DEFER`: #135 no dijo “todavía no tenemos tiempo”, sino que **la feature no encaja con el producto actual**.

## 3. Estado real de `main` al 29/08/2026

La arquitectura actual refuerza el rechazo:

- el club de Samuel es contenido/guía, no una plataforma con perfiles;
- lectores beta funciona como grupo pequeño y manual;
- `/lectores-beta/` declara que no hay comunidad pública, perfiles ni foro;
- no existe una identidad de lector propia que pueda poseer un badge;
- no existe un estado canónico “ha completado el club/serie” que el sitio pueda verificar de forma fiable.

Crear una insignia exigiría primero inventar o persistir ese estado.

## 4. Problemas que un badge aparentemente simple introduce

Para que una insignia tenga significado hay que responder:

- ¿quién es la persona?
- ¿cómo se autentica?
- ¿qué cuenta como completar?
- ¿quién valida la acción?
- ¿puede perder/repetir el logro?
- ¿dónde se guarda?
- ¿se muestra públicamente?
- ¿cómo se borra/exporta?
- ¿qué pasa si se hace trampa?
- ¿qué ocurre con menores?
- ¿hay accesibilidad/alternativa textual?
- ¿qué conducta intentamos mejorar?

Sin respuestas, la “micro-gamificación” es solo decoración con deuda de estado.

## 5. Riesgo editorial

El sitio busca una experiencia editorial/literaria, no un producto de retención basado en puntos.

Badges pueden:

- trivializar la participación;
- desplazar motivación intrínseca;
- introducir UI repetitiva;
- convertir lectura en checklist;
- generar jerarquías sociales artificiales;
- competir visualmente con libros, contenido y conversación real.

La palabra “discreto” no elimina estos problemas.

## 6. Alternativa aprobada: reconocimiento editorial real

Si una persona aporta algo valioso y existe permiso, pueden usarse mecanismos humanos como:

- agradecer a un club/mediador;
- citar una pregunta en un AMA editado;
- destacar una aportación con atribución autorizada;
- publicar conclusiones de una sesión;
- agradecer a lectores beta en el contexto adecuado;
- reconocer una colaboración concreta en una pieza editorial.

Ese reconocimiento tiene contexto y significado sin crear un sistema de puntos.

## 7. No usar localStorage como falso perfil

Una variante tentadora sería guardar badges solo en el navegador para evitar backend.

Eso tampoco resuelve la idea:

- no verifica la acción;
- se pierde/cambia por dispositivo;
- añade estado local sin valor portátil;
- puede crear expectativas de cuenta/progreso;
- introduce más storage que I.5 tendría que gobernar.

No persistir “logros” client-side solo para poder decir que existe gamificación.

## 8. Trigger extraordinario para reconsiderar

Aunque el estado es `REJECT`, una futura transformación real del producto podría justificar una nueva decisión distinta de J.4. Solo reevaluar si:

- existe comunidad propia estable;
- ya existe identidad por motivos independientes;
- hay una conducta concreta cuyo reconocimiento aporta valor;
- usuarios piden una forma de reflejar contribuciones;
- moderación/gobernanza están resueltas;
- la alternativa editorial simple resulta insuficiente.

Eso sería una nueva evaluación de producto, no “implementar J.4 pendiente”.

## 9. Relación con otras ideas

- **J.1:** no crear identidad/comunidad solo para posibilitar badges.
- **J.5:** AMA produce reconocimiento/contenido real sin gamificación.
- **J.6:** beta readers pueden recibir agradecimiento editorial sin sistema de logros.
- **I.5:** cualquier estado persistente añade datos/storage que deben justificarse.
- **L.4:** el rechazo conceptual es distinto del Badging API de PWA, pero ambos comparten falta de un estado real útil.

## 10. Qué no hacer

- No crear puntos, niveles, streaks o leaderboard.
- No añadir badges locales en `localStorage`.
- No inventar “completado” a partir de scroll.
- No pedir login para una insignia.
- No crear NFTs/códigos/credenciales digitales de participación.
- No usar badges para forzar newsletter/compartidos.
- No reetiquetar la idea como “fidelización” para saltarse el `REJECT`.

## 11. Definition of Done de esta decisión

Para J.4, cerrar correctamente significa:

- [ ] mantener `REJECT` en la autoridad;
- [ ] no abrir implementación/UI/storage;
- [ ] usar reconocimiento editorial contextual cuando sea apropiado;
- [ ] no crear identidad como dependencia de gamificación;
- [ ] si el producto cambia radicalmente, abrir una nueva evaluación desde requisitos actuales, no asumir que J.4 quedó pendiente.

## 12. Trazabilidad #135

Revisados:

- banco original J.4;
- revisión 108/108: `REJECT`;
- matriz final: `DESCARTAR` por necesidad no demostrada/tono;
- repo cross-check y overrides: alternativa de reconocimiento editorial real;
- autoridad machine-readable;
- autoridad humana final: `REJECT`;
- revalidación independiente: estados J mantenidos.

## 13. Cierre

J.4 se descarta porque no existe un progreso comunitario real que necesite representación. Si algún día aparece una comunidad madura, la pregunta deberá ser qué contribución merece reconocimiento; no cómo añadir badges a la web.