# 06 · Primeras evidencias reales del piloto — 21/10/2026

**Importante:** estas son **afirmaciones respaldadas por fuentes identificadas**, no fichas importadas, ni coordenadas comprobadas por el importador, ni imágenes autorizadas. Aún no se ha generado/públicado nada en la web. Los datos están listos para verificación humana final antes de ingresar en Sheets.

## Madrid: conexiones explícitas y lugares públicos

**Fuente primaria turística institucional:** [Turismo Madrid, Barrio de las Letras](https://www.esmadrid.com/barrios-de-madrid/barrio-letras) (consultada 21/10/2026).

| Candidato | Tipo de entidad | Qué afirma la fuente institucional | Relación provisional | Qué NO afirmar automáticamente |
| --- | --- | --- | --- | --- |
| Calle Álvarez Gato / callejón del Gato | calle (no punto exacto sin fuente geográfica) | Vinculada a un pasaje de **Luces de bohemia**, de Valle-Inclán, con espejos cóncavos y convexos | `ambientacion_literal` candidata, pendiente de contraste con texto/edición de obra | No atribuir cualquier local/espejo actual a la edición sin revisar |
| Casa Museo Lope de Vega | casa-museo pública | Casa vinculada a los últimos 25 años de vida de Lope y hoy museo | `vida_autor_publica` con persona Lope de Vega | No tratarlo como domicilio actual ni afirmar escenas de novelas |
| Calle de las Huertas | calle | Espacio del barrio con fragmentos de grandes escritores en pavimento | `homenaje`/cultura literaria | No inferir que las novelas se ambientaron allí |
| Ateneo de Madrid | institución cultural | Creado en 1835 como foro artístico, científico y literario | `institucion_cultural` | No inventar visita de autor/obra concreta |

**Fuente de localización e inventarios:** [Bibliotecas Madrid datos abiertos](https://datos.madrid.es/dataset/201747-0-bibliobuses-bibliotecas/downloads). Su presencia acredita biblioteca/dirección como candidato; hay que justificar aparte qué la hace emblemática.

**Próximos pasos de Madrid:** confirmar páginas oficiales del museo, accesibilidad y visita, localización precisa; elegir 1–2 librerías con historia contrastada y fuentes de su propio archivo/cronología; relacionar títulos usando referencias verificadas.

## París: oportunidad extraordinaria de fuente oficial

**Fuente municipal:** [Paris.fr, paseo por personajes literarios](https://www.paris.fr/pages/des-plaques-pour-commemorer-les-personnages-litteraires-de-paris-29191) (actualización 19/12/2025, consultada 21/10/2026). La ciudad describe **50 placas públicas** vinculadas a novelas/personajes; 30 nuevas anunciadas en diciembre de 2025 y su mapa interactivo institucional. Los siguientes son ejemplos extraídos de la lista oficial:

| Placa/parada pública | Obra y personaje según París | Vínculo sustentado | Cautela editorial |
| --- | --- | --- | --- |
| 4, place du Louvre | Madame de Clèves — *La Princesse de Clèves* (Madame de Lafayette) | `homenaje_placa` público en dirección indicada | NO declarar por ello que el personaje estuvo en esa dirección en la novela |
| 18, rue Ortolan | Rastignac — *Le Père Goriot* (Balzac) | `homenaje_placa` y relación ciudad/obra | No transformar emplazamiento de placa en escenario literal |
| 11, rue du Vieux-Colombier | D'Artagnan — *Les Trois Mousquetaires* (Dumas) | `homenaje_placa` y relación obra/personaje | No confundir placa de 2024 con hecho diegético |

Otra [nota municipal del 11/12/2025](https://www.paris.fr/pages/dans-le-5e-trois-nouvelles-plaques-pour-explorer-paris-via-des-personnages-litteraires-33286) documenta placas de Usbek, Jack Barnes y Astérix/Obélix. **El contenido municipal contextualiza la ficción**, pero cada placa es un homenaje público instalado hoy. Si la nota afirma además que determinada calle aparece en una obra, el vínculo `ambientacion_literal` exige su propia evidencia de texto/explicación específica.

**Conclusión comercial/editorial:** proyecto de destino París con 50 lugares verificables como *placas literarias*, más librerías/bibliotecas de interés cultural. Crear 50 fichas sería innecesario en el MVP: elegir inicialmente 3–5 con obra, autor y mapa comprobados; conservar las restantes como candidatos para investigación y búsqueda de citas, no copiar el listado entero sin revisar derechos y requisitos de reutilización del contenido.

## Una saga adaptada: reglas para evitar información falsa

**Caso futuro Juego de tronos**:
- `obra`: saga de novelas; el universo ficticio no es una ubicación geográfica visitable.
- `adaptacion`: serie audiovisual identificada por título/año/producción.
- `rodaje_adaptacion`: lugar real con prueba verificable de rodaje en episodio/temporada concretos; si proviene de oficina de turismo, confirmar la afirmación exacta.
- `inspiracion_documentada`: solo si una declaración del creador/autor o fuente sólida establece el vínculo.
- `vida_autor_publica`: solo museos, actos o lugares biográficos públicos, NUNCA domicilio actual.

No se incluyen aquí localizaciones concretas sin evidencia. **Prioridad:** recoger 2–3 conexiones diferentes para comprobar que la interfaz evita confundir novela, serie, rodaje y promoción.

## Etiquetado mínimo para cada ficha/hito

`lugar_id` · `destino_id` · `tipo_lugar` · `obra_id`/ `autor_id`/ `adaptacion_id` · `tipo_relacion` · `fuente_de_la_relacion` · `fecha_consulta` · `precision` · `estado_revision` · `derechos_foto` · `spoiler`

Campos que siguen **[[pendiente]]**: coordenadas específicas, licencia de imágenes, visita real/horarios/entradas, IDs del catálogo definitivo, traducciones autorizadas, aprobaciones humanas. Sin ellos, no subir como contenido publicado.
