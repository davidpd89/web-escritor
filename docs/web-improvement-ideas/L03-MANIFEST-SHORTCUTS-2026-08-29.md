# L.3 · Atajos PWA en `manifest.json`

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.

## Veredicto

#135 terminó concluyendo que los shortcuts ya existen en `manifest.json`. No hay que abrir una implementación nueva ni tratarlos como navegación esencial porque el soporte no es universal.

## Hipótesis original

Añadir shortcuts desde el icono instalado hacia destinos frecuentes como Cuaderno, Novedades o Club de lectura.

## Evolución histórica

### Revisión inicial → `ALREADY_COVERED`

La revisión ya localizó shortcuts en el manifest y recomendó mantenerlos.

### Matriz intermedia → `PILOTAR BAJO COSTE`

La matriz formuló temporalmente la idea como un posible piloto de shortcuts hacia Obras/Cuaderno/Herramientas si el soporte y la UX lo justificaban.

### Inspección profunda / autoridad final → `ALREADY_COVERED`

El cross-check del repositorio confirmó que el manifest ya publica shortcuts reales. La autoridad final cerró:

> «`manifest.json` ya contiene shortcuts. Mantener; soporte no universal.»

## Estado actual de `main`

`manifest.json` continúa declarando cuatro shortcuts:

1. **Las manecillas del recuerdo** → `/las-manecillas-del-recuerdo/`
2. **Todos los libros** → `/libros/`
3. **Cuaderno** → `/cuaderno/`
4. **Kit de prensa** → `/prensa.html`

Cada entrada incluye `name`, `short_name`, `url` y `description`.

Por tanto L.3 está materialmente implementada.

## Qué significa `ALREADY_COVERED`

- no crear otro manifest;
- no duplicar shortcuts con JS;
- no abrir un sistema de «quick actions» propio;
- mantener los shortcuts actuales cuando cambien prioridades;
- comprobar que las URLs continúan siendo canónicas y públicas.

## Soporte y arquitectura

Los shortcuts del Web App Manifest dependen del navegador/SO. Por eso:

- nunca deben ser la única forma de llegar a una sección;
- la navegación HTML principal sigue siendo autoridad;
- no deben esconder funcionalidades esenciales;
- el sitio debe funcionar exactamente igual sin instalación PWA.

## Cuándo revisar la selección

Reevaluar solo cuando cambie una prioridad editorial real, por ejemplo:

- una obra principal sustituye a otra;
- una URL deja de ser canónica;
- aparece una función recurrente claramente más útil;
- testing de PWA demuestra que un shortcut actual no aporta.

No rotarlos por campañas de pocos días si eso degrada estabilidad.

## Criterios de un buen shortcut

- destino estable;
- tarea frecuente;
- etiqueta corta comprensible;
- URL pública/canónica;
- no requiere sesión/estado;
- aporta incluso sin contexto previo.

## Relación con C.1

El lanzamiento de Manecillas puede justificar que la obra figure entre los shortcuts, pero C.1 no debe convertir el manifest en espacio publicitario rotatorio.

## Relación con L.1/L.2/L.4

Los shortcuts no implican Push, Badging ni offline-first. Son una capacidad independiente ya cubierta.

## QA futuro

- JSON válido;
- URLs internas existentes;
- `start_url`/`scope` coherentes;
- iconos válidos;
- nombres legibles;
- no más shortcuts de los que la plataforma pueda presentar útilmente;
- navegación normal equivalente.

## Qué NO hacer

- añadir shortcut por cada sección;
- usar enlaces externos como shortcut principal sin razón;
- depender de ellos para tareas esenciales;
- crear iconos nuevos solo por completar checklist;
- cambiar el manifest en cada campaña;
- confundir shortcuts con enlaces del header/footer.

## Trazabilidad preservada

- hipótesis original;
- revisión que localiza implementación;
- matriz `PILOTAR BAJO COSTE`;
- override profundo de repo;
- autoridad final `ALREADY_COVERED`;
- manifest actual con cuatro shortcuts;
- revalidación independiente.

## Recomendación para Clara/Claude

**No implementar nada nuevo para L.3.** Mantener `manifest.json` como autoridad y revisar shortcuts únicamente cuando cambien destinos estables o una auditoría PWA detecte un problema real.