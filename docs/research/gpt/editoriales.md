# Revisión de editoriales y contactos — PR #692

Estado comprobado el 22/10/2026. Herramientas de revisión utilizables por CLI;
la publicación del directorio sigue siendo responsabilidad del builder existente.
No se envían correos ni se modifica el directorio automáticamente.

## Alcance que se integra

| Módulo | Función comprobada | Límite |
| --- | --- | --- |
| `gpt_editoriales_reconcile.py` | Concilia directorio, sellos y libros; detecta referencias rotas, nombres coincidentes y duplicados. | Un sello con libros no demuestra recepción de originales. |
| `gpt_editoriales_contact_evidence.py` | Valida observaciones, hosts, fechas y alcance; extrae candidatos de cinco páginas oficiales mediante el `CachedHTTP` existente. | Las expresiones de extracción son específicas de esas cinco URL. El correo extraído y el estado requieren revisión humana. |
| `gpt_editoriales_review_plan.py` | Combina los dos informes y genera una cola determinista, con identificadores estables, prioridades y bloqueos. | No genera parches ni aprueba contactos o cambios de estado. |

Se revisaron los cinco módulos originales y se ejecutaron sus **111 tests** sobre
el checkout completo, localmente y en el [job original aprobado](https://github.com/davidpd89/web-escritor/actions/runs/39803704906).
Se retiran del código el adaptador Wikidata y el simulador de aprobación por campo:
solo tenían pruebas sintéticas y no aportaban una integración utilizada. Sus
conclusiones útiles se conservan abajo. Tras la reducción y las correcciones hay
**86 tests**, incluido un recorrido de los tres módulos con los datos reales del repositorio.

## Verificación real

[Resultados estructurados y hashes de los cuerpos oficiales](editoriales-verificacion-real-2026-10-22.json).
El piloto descargó HTML original mediante `CachedHTTP`, respetando robots y su
presupuesto: **9 solicitudes físicas, 0 aciertos de caché, 0 fallos, 5/5 coincidencias**.
Se repitió la extracción sobre esos mismos cuerpos desde disco: **5/5**, sin red.
El replay sintético con el cliente HTTP de producción también está cubierto por unittest.

| Fuente oficial | Resultado del piloto | Contacto para manuscritos |
| --- | --- | --- |
| [Anagrama](https://www.anagrama-ed.es/manuscritos) | Pausa, específica de la editorial. | Ninguno extraído. |
| [Nocturna](https://www.nocturnaediciones.com/contacto) | Abierto; la limitación de formato físico no lo convierte en cierre. | Candidato coincidente con la ficha; separado de prensa. |
| [Minotauro](https://www.planetadelibros.com/editorial/minotauro/21) | Abierto, específico del sello. | Candidato coincidente con la ficha. |
| [Alienta](https://www.planetadelibros.com/editorial/alienta-editorial/15) | Abierto para ensayo; no implica aceptación de novelas. | Coincide con la candidata, excluida de publicación. |
| [PRH / Alfaguara](https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/) | Canal general del grupo. | No infiere correo ni aceptación de Alfaguara. |

El builder real valida las 150 fichas más Alienta en una copia temporal; comprueba
su exclusión con `publish=false` y valida la variante publicable sin escribir páginas.
No se actualizan Nocturna ni Minotauro: esas modificaciones de datos pertenecen a #722.

El recorrido completo concilia **150 editoriales, 11 sellos y 55 libros**, sin
referencias rotas ni nombres normalizados duplicados. Las **18 observaciones**
revisadas generan **42 tareas**: 9 verificaciones de sellos, 5 revisiones de canales,
24 reverificaciones por antigüedad y 4 entidades fuera del directorio que requieren
resolver su identidad. Estas cuatro son sellos bibliográficos; el bloqueo evita
crearlos automáticamente como editoriales receptoras. Dos sellos sin libros se aplazan.

Se prueban rechazos por ID duplicado, la misma evidencia con otro ID, libros
duplicados, fechas inválidas/futuras/caducadas, dominios ajenos, contradicciones,
texto oculto y cierres alejados de instrucciones antiguas. Una evidencia caducada
provoca revisión, nunca cierre automático. Estados: 45 días de vigencia; contactos:
180 días. Los informes de revisión no copian correos.

## Uso reproducible

Python 3.12 en Linux, sin dependencias nuevas. En Windows el builder requiere
datos de zona horaria `tzdata`. Ejecutar desde la raíz del checkout completo:

```bash
python -m unittest discover -s tests -p 'test_gpt_editoriales_*.py' -v
mkdir -p .ci/reading-intake
python scripts/research/gpt_editoriales_reconcile.py --directory data/editoriales.json --catalogue-publishers data/reading-publishers.json --books data/reading-catalogue.json --as-of 2026-10-22 > .ci/reading-intake/identities.json
python scripts/research/gpt_editoriales_contact_evidence.py --observations docs/research/gpt/editoriales-e4-observaciones-2026-10-22.json --trusted-hosts docs/research/gpt/editoriales-e4-trusted-hosts-2026-10-22.json --as-of 2026-10-22 > .ci/reading-intake/evidence.json
python scripts/research/gpt_editoriales_review_plan.py --directory data/editoriales.json --identities .ci/reading-intake/identities.json --evidence .ci/reading-intake/evidence.json --as-of 2026-10-22 --max-tasks 100 > .ci/reading-intake/review-plan.json
```

El piloto de red es optativo y no se ejecuta en CI:

```bash
python scripts/research/gpt_editoriales_contact_evidence.py --live-pilot --pilot-cases docs/research/gpt/editoriales-piloto-5-fuentes-2026-10-22.json --trusted-hosts docs/research/gpt/editoriales-e4-trusted-hosts-2026-10-22.json --as-of 2026-10-22 --budget 12 --cache-dir .ci/official-html-cache --output .ci/reading-intake/live-pilot.json
```

La fecha anterior reproduce esta evaluación histórica; una revisión posterior
requiere contrastar fuentes y renovar observaciones. La fecha de análisis no
sustituye la fecha original de descarga, que el informe conserva por separado.
El workflow específico se activa en PR y en `push` a `main` cuando cambian sus
entradas o dependencias. Solo lee el checkout; no usa secretos ni fuentes externas.

## Límites y seguimiento

- La comprobación de un correo es una coincidencia con instrucciones oficiales,
  no una prueba de entrega ni una autorización para contactar.
- El parser no ejecuta JavaScript ni resuelve hojas CSS externas. Cambios de texto,
  diseños nuevos y fuentes adicionales requieren casos contrastados; `unknown`
  conserva la necesidad de revisión.
- Los workflows generales fallaban en `test-npm-supply-chain-baseline.py` por la
  alerta nueva `GHSA-rxp7-6hxx-x8q5` de `ip-address`. El lockfile y el registro son
  idénticos a `main`; esta PR no duplica la corrección global de las otras ramas.
  El estado del último SHA debe consultarse en Actions antes del merge.

Conclusiones preservadas de los módulos retirados: Wikidata puede proponer
identidades desde snapshots, nunca acreditar recepción ni contactos. Una decisión
`approve` dentro de JSON no autentica a un revisor; la publicación futura necesita
revisión real del diff y evidencia vigente. No se introduce un segundo publicador.
[Contrato histórico por campo](editoriales-e6-contrato-2026-10-22.md),
[observaciones de fuentes](editoriales-e4-resultados-2026-10-22.md) y
[diseño histórico de integración](editoriales-e5-integracion-2026-10-22.md)
se conservan como investigación, no como estado actual de implementación.
