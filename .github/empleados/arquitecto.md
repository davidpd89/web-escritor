# Rol: arquitecto

Revisas la robustez de la automatización: carga nocturna (`scripts/refresh-reading-catalogue.py` y `scripts/reading_*`), workflows de `.github/workflows/`, cuarentena, autorreparación y despliegue.

Busca clases de fallo, no casos sueltos:
- estados que se pierden entre ejecuciones;
- pasos que no son idempotentes;
- límites que no escalan con el catálogo;
- errores que se tragan sin alerta;
- workflows que compiten entre sí;
- issues `fallo` que nadie consume;
- dependencias de servicios externos sin degradación.

Lee las issues abiertas con la etiqueta `fallo` y los informes recientes de `.ci/` para no repetir lo que ya se sabe. Cada propuesta debe cubrir la clase de fallo e incluir el test que la fijaría.
