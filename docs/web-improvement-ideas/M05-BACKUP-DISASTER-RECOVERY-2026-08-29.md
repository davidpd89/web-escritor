# M.5 · Backup independiente / disaster recovery del contenido

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `CONDITIONAL`.

## Veredicto

#135 corrige una premisa importante: **Git remoto ya es un backup fuerte del contenido versionado**. Un segundo backup solo aporta si cubre un escenario de fallo definido —por ejemplo, borrado/compromiso de cuenta/repositorio— y si se demuestra que puede restaurarse.

No se debe copiar PII o secretos “por seguridad” a otro sitio sin cifrado, retención y necesidad.

## Hipótesis original

La idea proponía copias exportables del contenido editorial fuera del repositorio Git, especialmente `content-registry.json`, Markdown/HTML y autoridades editoriales, como defensa distinta frente a corrupción de repo.

## Evolución en #135

### Revisión

La revisión detectó que GitHub ya proporciona versionado/remoto y que un backup adicional necesita justificar su escenario.

### Matriz → `DEFERIR/POLÍTICA`

La matriz señaló:

> Git remoto ya es fuerte para contenido; backup adicional solo para escenarios claros y cifrado si contiene datos no públicos.

### Autoridad final → `CONDITIONAL`

La autoridad final mantiene M.5 como condicional:

> snapshot independiente cifrado + restore drill puede aportar DR ante borrado/cuenta comprometida; evitar duplicar PII.

### Revalidación independiente

M.1–M.5 se mantienen. No aparece evidencia que convierta M.5 en obligación inmediata.

## Qué protege Git actualmente

Para archivos commiteados:

- historia de cambios;
- ramas;
- commits reproducibles;
- remoto fuera del dispositivo local;
- capacidad de volver a un SHA anterior.

Por eso “hacer ZIP periódico porque sí” puede ser menos fiable que Git si nunca se prueba su restauración.

## Escenarios que sí podrían justificar una segunda copia

1. compromiso/borrado de la cuenta GitHub;
2. eliminación accidental del repo remoto;
3. corrupción lógica propagada al remoto y detectada tarde;
4. necesidad legal/operativa de conservar snapshots inmutables;
5. recuperación sin depender de una única cuenta/proveedor.

## Qué debería incluir

Preferir **contenido público/versionado y autoridades necesarias para reconstruir el sitio**:

- código y HTML/Markdown versionado;
- `data/*.json` canónicos;
- scripts/builders;
- configuración pública necesaria;
- documentación operativa no sensible.

## Qué NO debe copiarse automáticamente

- secrets/API keys;
- exports de Brevo con suscriptores;
- PII de formularios;
- prompts/conversaciones privadas;
- `.env` reales;
- backups de terceros que ya contienen información sensible sin necesidad.

Si un backup debe incluir material privado, cifrado y control de acceso son requisitos previos.

## Diseño mínimo de DR

Una política útil debe especificar:

```text
scenario
source of truth
backup scope
frequency
retention
storage location
owner
encryption requirement
restore procedure
last restore drill
```

Sin restore drill, “tenemos backup” no es evidencia suficiente.

## Estrategia por capas

### Capa 1 · Git remoto

Autoridad principal para el contenido versionado.

### Capa 2 · snapshot independiente opcional

Solo si el riesgo lo justifica. Puede ser otro remoto privado, archivo cifrado o export reproducible.

### Capa 3 · datos externos

Brevo, Search Console, Metricool, etc. tienen políticas/exportaciones propias. No mezclar sus datos personales con el backup del sitio salvo necesidad separada.

## Restore drill

Prueba recomendada:

1. elegir snapshot/commit;
2. restaurar en directorio/entorno aislado;
3. ejecutar build/checks;
4. verificar assets/autoridades esenciales;
5. documentar tiempo, errores y dependencias faltantes;
6. no publicar el restore accidentalmente.

## Relación con I.5

Data minimization aplica también a backups: retener una copia histórica de datos personales puede contradecir una política de borrado. M.5 debe respetar las autoridades de privacidad, no invalidarlas.

## Relación con Q.4/runbooks

Los runbooks de lanzamiento pueden formar parte del contenido versionado, pero M.5 no debe crear una segunda colección de runbooks.

## Riesgos

- backup sin cifrar;
- copiar secrets;
- snapshots imposibles de restaurar;
- retención infinita de PII;
- múltiples copias divergentes tratadas como source of truth;
- automatización que publica/expone el backup;
- depender del mismo proveedor/cuenta para “backup independiente”.

## Trigger válido

```text
explicit failure scenario
AND scope defined
AND storage independent enough for that scenario
AND sensitive-data policy
AND restore drill feasible
```

## Trazabilidad

- backlog original M.5;
- revisión 108/108;
- matriz `DEFERIR/POLÍTICA`;
- autoridad final `CONDITIONAL`;
- revalidación independiente.

## Recomendación

Mantener Git como autoridad. Solo añadir una segunda copia cuando se defina qué desastre cubre y se pueda demostrar restauración; no duplicar información sensible por inercia.