# C.10 · Archivo de prensa/menciones centralizado y con fecha

Fecha de reconstrucción: 2026-08-29  
Fuente histórica principal: PR #135, snapshot íntegro `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `IMPLEMENT_AFTER_CURRENT_DEBT`.  
Revalidación contra `main`: `prensa.html` ya es un kit de prensa sólido, pero no se ha localizado un archivo cronológico completo de menciones externas con `verifiedAt`; C.10 sigue siendo trabajo neto, sin crear una segunda página de prensa.

## 1. Hipótesis original

La lista inicial proponía ampliar `prensa.html` con un registro cronológico de cada mención, entrevista o reseña externa, enlazada a la fuente, con la idea de convertir el media kit en una superficie viva de corroboración externa.

El valor defendible no es «E-E-A-T por acumular enlaces». Es:

- ofrecer a periodistas/lectores una cronología verificable;
- conservar fuentes externas reales sobre el autor y las obras;
- detectar y corregir hechos desactualizados;
- reutilizar evidencia real en bio/prensa sin fabricar autoridad.

## 2. Evolución en #135

### Primera revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

`IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` exige:

- menciones reales;
- fecha;
- medio;
- URL fuente;
- `verifiedAt`;
- utilidad para corroboración externa y press kit.

No se presenta como factor de ranking directo.

### Matriz intermedia → `IMPLEMENTAR`

`IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` conserva la idea como trabajo válido:

> archivo de prensa real y cronológico + URL fuente + fecha + medio + tipo.

### Autoridad final → `IMPLEMENT_AFTER_CURRENT_DEBT`

`PR135-FINAL-AUTHORITY-2026-08-28.md` vuelve a situarla detrás de la deuda vigente:

> «Archivo cronológico de prensa con medio, fecha, tipo y URL fuente real; no fabricar autoridad.»

### Revalidación independiente

La falsación final mantiene C.1–C.10; no aparece evidencia que rebaje C.10 a `REJECT`, `DEFER` o `ALREADY_COVERED`.

## 3. Diferencia entre kit de prensa y archivo de prensa

`prensa.html` actual ya contiene:

- bio corta/larga;
- datos del autor;
- fichas técnicas;
- imágenes y materiales;
- contacto para medios;
- navegación a eventos/premios/ferias.

Eso es un **press kit**.

C.10 añade otra función dentro de la misma autoridad: un **registro factual de apariciones externas**. No justifica `/archivo-prensa/`, `/media/` u otra landing si `prensa.html` puede albergarlo coherentemente.

## 4. Modelo de registro recomendado

Si se materializa una fuente de datos, mínimo:

```json
{
  "id": "medio-fecha-slug",
  "type": "INTERVIEW",
  "medium": "Nombre del medio",
  "title": "Título real de la pieza",
  "publishedAt": "YYYY-MM-DD",
  "url": "https://fuente.example/...",
  "about": ["David Porto Díaz", "Samuel entre mundos"],
  "verifiedAt": "YYYY-MM-DD",
  "status": "VERIFIED"
}
```

Tipos posibles, sin sobre-modelar:

```text
INTERVIEW
REVIEW
PRESS_MENTION
CATALOG_PROFILE
PODCAST
RADIO_TV
EVENT_COVERAGE
```

Una red social no debe elevarse automáticamente a «prensa».

## 5. Verificación

Antes de registrar:

1. abrir la fuente original;
2. confirmar que se refiere al David/libro correcto;
3. guardar título, medio y fecha publicados por la fuente;
4. usar la URL final/canónica cuando sea posible;
5. registrar `verifiedAt` independientemente de `publishedAt`;
6. no transcribir elogios largos ni ratings sin permiso/contexto;
7. marcar fuentes caídas/redirects sin falsificar la fecha histórica.

## 6. Hallazgo posterior R.50 · Google Alerts

La novena pasada de #135 añadió una operación externa gratuita específicamente útil para C.10.

Alertas propuestas:

```text
"David Porto Díaz"
"Las manecillas del recuerdo" "David Porto"
"Samuel entre mundos" "David Porto"
```

Opcional solo si produce señal:

```text
"Noveris" "David Porto"
```

Runbook histórico:

```text
abrir fuente
→ confirmar identidad
→ clasificar PRENSA | RESEÑA | CATÁLOGO | RED SOCIAL | SPAM | DUPLICATE
→ registrar solo autoridad útil con URL + fecha + medio + verifiedAt
→ corregir hechos si procede
```

Google Alerts detecta candidatos; **no es autoridad de verdad ni monitor exhaustivo**.

## 7. Hallazgo posterior R.20 · link reclamation

La sexta pasada añadió un uso complementario de las menciones externas:

- detectar URL antigua/404;
- dato factual incorrecto;
- enlace a host/HTTP obsoleto;
- backlink a una página retirada con reemplazo inequívoco.

La corrección debe solicitar URL/dato correcto, no anchor text. C.10 puede alimentar ese workflow; no debe convertirse en campaña automatizada de backlinks.

## 8. Structured data y reviews

La investigación primaria de #135 recuerda que Google no permite agregar ratings/reviews de otros sitios como si fueran propios para fabricar review snippets.

Por tanto:

- enlazar una reseña externa real: sí;
- resumir factual y brevemente con atribución: cuando aporte;
- copiar estrellas/agregados ajenos a JSON-LD propio: no;
- presentar una mención como endorsement si no lo es: no.

## 9. Revalidación de `main`

A fecha 2026-08-29, `prensa.html` es una superficie canónica madura de kit de prensa, pero la inspección realizada no localiza un registro cronológico general con medio + fecha + tipo + URL externa + `verifiedAt`.

Conclusión actual:

```text
press kit existente = ALREADY_COVERED
archivo histórico C.10 = IMPLEMENT_AFTER_CURRENT_DEBT
```

No confundir ambas capas.

## 10. Implementación correcta futura

Preferencia:

```text
una autoridad de datos
→ builder/validación
→ sección en prensa.html
→ enlaces externos reales
```

No hardcodear una lista creciente en múltiples HTML si el volumen ya justifica datos estructurados.

Campos/checks útiles:

- `publishedAt` válido;
- `verifiedAt >= publishedAt` cuando aplique;
- URL HTTPS salvo fuente histórica excepcional;
- sin duplicados por canonicalización;
- clasificación estable;
- enlaces rotos reportados, no borrados silenciosamente si tienen valor histórico.

## 11. UX

La cronología debería permitir escanear:

- año/fecha;
- tipo;
- medio;
- obra/tema;
- destino externo claramente identificado.

No necesita filtros complejos con pocas entradas. Escalar interacción solo si el archivo crece.

## 12. Qué NO hacer

- inventar menciones;
- registrar autopublicaciones propias como cobertura externa;
- llamar «reseña» a una ficha comercial;
- copiar reseñas completas;
- contar backlinks como prueba de autoridad;
- crear otra página de prensa;
- usar menciones no verificadas;
- borrar una fuente histórica solo porque hoy devuelve 404 sin registrar su estado;
- automatizar outreach desde CI.

## 13. Pasadas posteriores de #135 revisadas

- cuarta/quinta: sin cambio específico de C.10;
- sexta: R.20 añade link reclamation legítimo;
- séptima/octava: sin override específico;
- novena: R.50 añade Google Alerts como descubrimiento;
- décima–decimoquinta: no cambian el estado final;
- revalidación independiente mantiene C.10.

## 14. Trazabilidad

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original;
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — primer estado;
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR` intermedio;
- `IDEAS-MEJORA-WEB-SEXTA-PASADA-2026-08-28.md` — R.20;
- `IDEAS-MEJORA-WEB-NOVENA-PASADA-GRATUITA-2026-08-28.md` — R.50;
- `data/web-improvement-decisions-2026-08-28.json` — decisión machine-readable;
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — final;
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — falsación;
- `prensa.html` actual — reconciliación de repo.

## 15. Definition of Done de la reconstrucción

- [x] hipótesis original preservada;
- [x] estados intermedio/final preservados;
- [x] diferencia press kit/archive explicitada;
- [x] R.20 y R.50 integrados;
- [x] políticas anti-review-schema/backlink preservadas;
- [x] estado actual contrastado;
- [x] sin nueva implementación prematura.

## Recomendación para Clara/Claude

C.10 sigue siendo trabajo válido **después de la deuda prioritaria**. Cuando se implemente, ampliar `prensa.html` y crear una única autoridad factual/cronológica; no construir otra estrategia de prensa paralela.