# D.4 · Revalidación de producción — leer después / posición personal

Fecha: 2026-08-30  
Base comprobada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## Veredicto

**CONDITIONAL · NO_USER_STATE_OWNER · EDITORIAL_READING_LIST_IS_NOT_READ_LATER · DEMAND_TRIGGER_NOT_MET · NO_CODE**

No existe evidencia suficiente para crear favoritos/read-later propios del sitio. La coincidencia nominal `data/reading-list.json` no es estado de visitantes y no debe usarse para declarar D.4 parcialmente implementada.

## Evidencia directa

`data/reading-list.json` contiene un dataset editorial con campos como:

- `title`;
- `author`;
- `publish`;
- `note`;
- `status`;
- `started_on`;
- `link_kind`;
- `url`;
- `verified_on`.

El registro actual incluso usa una URL `editorial.example` y `publish:false`, lo que confirma su naturaleza de fixture/dato editorial, no una lista privada del navegador de cada lector.

No es:

- localStorage de usuario;
- favoritos personales;
- historial de lectura;
- posición de scroll;
- sincronización entre dispositivos.

## Problema no demostrado

Para crear estado persistente del visitante debe demostrarse primero una fricción real: lectores recurrentes que quieran volver a piezas concretas y para quienes el navegador/marcadores actuales no sean suficientes en el journey observado.

En esta revalidación no se recupera esa evidencia de demanda.

## Si algún día se reabre

La primera versión debe ser deliberadamente mínima:

```json
{
  "schemaVersion": 1,
  "items": [
    {
      "url": "/cuaderno/.../",
      "savedAt": "ISO-8601"
    }
  ]
}
```

Principios:

- guardar URL/ID canónico, no copia del artículo;
- local-only antes que cuenta/backend;
- eliminación visible;
- no enviar la lista a analytics;
- no mezclar favoritos con manuscritos, emails ni PII;
- progressive enhancement: leer sigue funcionando sin JS.

## Posición de lectura sigue fuera del MVP

`Guardar para después` y `recordar scroll` son dos necesidades diferentes. Restaurar posición introduce problemas con cambios editoriales, imágenes, hashes, history y múltiples dispositivos.

No se añade junto al favorito por conveniencia técnica.

## Límites con otras capacidades

- D.1 puede confirmar `Guardado`, pero no justifica D.4.
- D.3 muestra progreso actual, no persiste estado.
- L.2/PWA puede cachear páginas visitadas; eso no convierte una URL guardada en contenido offline.
- `data/reading-list.json` sigue siendo editorial y no se reutiliza como almacén privado.

## Trigger

```text
repeated reader need
AND sufficient recurring content
AND local-only solves the journey
AND clear delete/control
AND privacy contract
AND no conflict with browser/PWA behavior
```

Hasta entonces no existe un owner de datos de usuario que merezca introducirse.

## Decisión final

D.4 permanece correctamente condicionada. No se implementa por simetría con plataformas de lectura ni por la presencia de un fichero editorial con nombre parecido.

**Estado final: `CONDITIONAL · NO_USER_STATE_OWNER · EDITORIAL_READING_LIST_IS_NOT_READ_LATER · DEMAND_TRIGGER_NOT_MET · NO_CODE`.**
