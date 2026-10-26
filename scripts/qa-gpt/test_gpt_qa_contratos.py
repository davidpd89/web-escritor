import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de qa_contratos: HTML, sitemap, seguridad y escala."""

import tempfile
import time
import unittest
from unittest.mock import patch

import qa_contratos as qc


class ContratosRegresion(unittest.TestCase):
    def setUp(self):
        """Aisla todas las paginas y sitemaps del repositorio real."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        self.original_site = qc.SITE
        self.addCleanup(setattr, qc, "SITE", self.original_site)
        qc.SITE = "https://davidportodiaz.com"

    def escribir(self, ruta, contenido):
        p = self.root / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        return p

    def html(self, body="", head="", lang="es"):
        return (
            '<!doctype html><html lang="' + lang + '"><head>'
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width">'
            '<title>Pagina de prueba de contratos</title>'
            '<meta name="description" content="'
            + "Descripcion de prueba suficientemente larga para verificar contratos SEO."
            + '">'
            + head
            + '</head><body>'
            + '<header><nav><a href="/">Inicio</a></nav></header>'
            + '<main id="contenido"><h1>Pagina de prueba</h1>'
            + body
            + '</main></body></html>'
        )

    def pagina(self, ruta="editoriales/ejemplo/index.html", body="", head=""):
        return self.escribir(ruta, self.html(body, head))

    def contexto(self, ruta, en_sitemap=True):
        p = qc.leer(self.root, ruta)
        return {
            "p": p,
            "ruta": ruta,
            "root": self.root,
            "url": qc.url_de(self.root, ruta),
            "en_sitemap": en_sitemap,
        }

    def sitemap(self, urls, nombre="sitemap.xml"):
        contenido = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(
                "<url><loc>" + u + "</loc></url>"
                for u in urls
            )
            + "</urlset>"
        )
        return self.escribir(nombre, contenido)

    def correr(self, rutas, contratos=None):
        if contratos is None:
            contratos = qc.CONTRATOS
        return qc.correr(
            self.root,
            {"editoriales": rutas},
            contratos=contratos,
        )

    def causas(self, resultado):
        return {g["causa"] for g in resultado["grupos"]}

    def test_smoke_contrato_completo_sin_falsos_positivos(self):
        """Evita que una pagina valida produzca hallazgos espurios."""
        ruta = self.pagina(
            head=(
                '<link rel="canonical" '
                'href="https://davidportodiaz.com/editoriales/ejemplo/">'
                '<meta name="robots" content="index,follow">'
                '<meta property="og:title" content="Pagina de prueba">'
                '<meta property="og:description" content="Descripcion">'
                '<meta property="og:image" content="https://example.com/a.jpg">'
                '<meta property="og:url" '
                'content="https://davidportodiaz.com/editoriales/ejemplo/">'
                '<script type="application/ld+json">'
                '{"@context":"https://schema.org","@type":"WebPage"}'
                '</script>'
            )
        )
        self.escribir("index.html", self.html())
        self.sitemap([qc.url_de(self.root, ruta)])

        resultado = self.correr([ruta])

        self.assertEqual(resultado["paginas"], 1)
        self.assertEqual(resultado["fallos_brutos"], 0)
        self.assertEqual(resultado["fallos_unicos"], 0)
        self.assertEqual(resultado["grupos"], [])

    def test_parser_conserva_texto_de_encabezados_anidados(self):
        """Evita perder encabezados cuando contienen enlaces o etiquetas."""
        ruta = self.pagina(
            body='<h2>Editorial <span>de <em>fantasia</em></span></h2>'
        )

        p = qc.leer(self.root, ruta)

        self.assertIn(
            ("h2", "Editorial de fantasia"),
            p.h,
        )

    def test_parser_no_confunde_script_normal_con_jsonld(self):
        """Evita analizar JavaScript ordinario como datos estructurados."""
        ruta = self.pagina(
            body=(
                '<script>const x = {"@type":"Fake"};</script>'
                '<script type="application/ld+json">'
                '{"@type":"Book"}'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertEqual(tipos, ["Book"])
        self.assertEqual(malos, 0)

    def test_jsonld_malformado_no_oculta_bloque_valido(self):
        """Evita que un bloque JSON-LD corrupto invalide los restantes."""
        ruta = self.pagina(
            body=(
                '<script type="application/ld+json">{mal</script>'
                '<script type="application/ld+json">'
                '{"@type":"Book"}'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertEqual(tipos, ["Book"])
        self.assertEqual(malos, 1)

    def test_jsonld_graph_con_varios_tipos(self):
        """Evita perder entidades cuando JSON-LD utiliza @graph."""
        ruta = self.pagina(
            body=(
                '<script type="application/ld+json">'
                '{"@context":"https://schema.org","@graph":['
                '{"@type":["Book","CreativeWork"]},'
                '{"@type":"Person"}'
                ']}'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertEqual(malos, 0)
        self.assertCountEqual(
            tipos,
            ["Book", "CreativeWork", "Person"],
        )

    def test_jsonld_array_de_entidades(self):
        """Evita descartar JSON-LD cuya raiz es una lista valida."""
        ruta = self.pagina(
            body=(
                '<script type="application/ld+json">'
                '[{"@type":"Book"},{"@type":"Person"}]'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertEqual(malos, 0)
        self.assertCountEqual(tipos, ["Book", "Person"])

    # BUG: Un JSON-LD valido sintacticamente con raiz escalar puede
    # provocar TypeError e interrumpir la auditoria de todas las paginas.
    # Arreglo minimo: validar dict/list antes de recorrer la raiz y
    # registrar como malformados los bloques con estructura incompatible.
    def test_jsonld_raiz_escalar_no_interrumpe_auditoria(self):
        """Evita que JSON-LD inesperado aborte la auditoria completa."""
        ruta = self.pagina(
            body=(
                '<script type="application/ld+json">42</script>'
                '<script type="application/ld+json">'
                '{"@type":"Book"}'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertIn("Book", tipos)
        self.assertGreaterEqual(malos, 1)

    # BUG: @graph puede ser null, numero u otro tipo incompatible.
    # El recorrido actual no valida su estructura y puede lanzar TypeError.
    # Arreglo minimo: comprobar que @graph sea una lista antes de iterar;
    # registrar el bloque invalido sin interrumpir los restantes.
    def test_jsonld_graph_no_iterable_no_aborta(self):
        """Evita detener un lote por un @graph mal tipado."""
        ruta = self.pagina(
            body=(
                '<script type="application/ld+json">'
                '{"@graph":null}'
                '</script>'
            )
        )

        tipos, malos = qc.tipos_jsonld(qc.leer(self.root, ruta))

        self.assertEqual(tipos, [])
        self.assertGreaterEqual(malos, 1)

    def test_canonical_diferente_se_detecta(self):
        """Evita aceptar canonicals que apuntan a otra ficha."""
        ruta = self.pagina(
            head=(
                '<link rel="canonical" '
                'href="https://davidportodiaz.com/editoriales/otra/">'
            )
        )

        fallos = qc.c_canonical(self.contexto(ruta))

        self.assertTrue(fallos)
        self.assertIn("canonical distinto", fallos[0][0])

    def test_canonical_con_fragmento_no_se_acepta(self):
        """Evita aceptar un canonical contaminado por fragmentos."""
        ruta = self.pagina(
            head=(
                '<link rel="canonical" '
                'href="https://davidportodiaz.com/editoriales/ejemplo/#detalle">'
            )
        )

        fallos = qc.c_canonical(self.contexto(ruta))

        # Un canonical con fragmento no debe considerarse equivalente
        # al canonical limpio. El codigo ya detecta la diferencia.
        # La asercion original estaba invertida.
        self.assertTrue(fallos)
        self.assertTrue(
            any("canonical distinto" in causa for causa, _ in fallos)
        )

    def test_robots_noindex_en_sitemap_es_incidencia(self):
        """Evita publicar en sitemap paginas declaradas noindex."""
        ruta = self.pagina(
            head='<meta name="robots" content="noindex,nofollow">'
        )

        fallos = qc.c_robots(self.contexto(ruta, en_sitemap=True))

        self.assertTrue(fallos)
        self.assertIn("noindex", fallos[0][0])

    def test_robots_noindex_fuera_sitemap_no_es_incidencia(self):
        """Evita marcar como error paginas excluidas deliberadamente."""
        ruta = self.pagina(
            head='<meta name="robots" content="noindex,follow">'
        )

        fallos = qc.c_robots(self.contexto(ruta, en_sitemap=False))

        self.assertEqual(fallos, [])

    def test_imagen_interna_ausente_y_alt_ausente(self):
        """Evita perder simultaneamente errores de imagen y accesibilidad."""
        ruta = self.pagina(
            body='<img src="/assets/portada-inexistente.jpg">'
        )

        fallos = qc.c_imagenes(self.contexto(ruta))
        causas = [causa for causa, _ in fallos]

        self.assertIn("<img> sin atributo alt", causas)
        self.assertIn("imagen interna inexistente", causas)

    def test_imagen_interna_existente_no_da_error(self):
        """Evita falsos positivos con imagenes locales presentes."""
        self.escribir("assets/portada.jpg", "imagen simulada")
        ruta = self.pagina(
            body='<img src="/assets/portada.jpg" alt="Portada">'
        )

        self.assertEqual(
            qc.c_imagenes(self.contexto(ruta)),
            [],
        )

    def test_enlace_relativo_con_query_resuelve(self):
        """Evita considerar rotos enlaces validos con parametros."""

        # Correccion del TEST, no del codigo:
        # html() incluye siempre un enlace de navegacion href="/".
        # El fixture anterior no creaba index.html y c_enlaces()
        # detectaba correctamente ese enlace roto.
        # Se crea la portada para aislar el enlace que se quiere probar.
        self.escribir("index.html", self.html())

        self.escribir(
            "editoriales/destino/index.html",
            self.html(),
        )

        ruta = self.pagina(
            body='<a href="../destino/?origen=catalogo">Destino</a>'
        )

        fallos = qc.c_enlaces(self.contexto(ruta))

        self.assertEqual(fallos, [])

    def test_ancla_interna_inexistente_se_detecta(self):
        """Evita aceptar enlaces de salto sin elemento de destino."""
        ruta = self.pagina(
            body='<a href="#seccion-ausente">Ir a seccion</a>'
        )

        fallos = qc.c_enlaces(self.contexto(ruta))

        self.assertIn(
            "ancla interna sin destino",
            [causa for causa, _ in fallos],
        )

    # BUG: Los fragmentos se comparan literalmente, sin percent-decoding.
    # Esto produce falsos positivos para identificadores Unicode validos.
    # Arreglo minimo: aplicar urllib.parse.unquote al fragmento antes
    # de buscar el ID de destino.
    def test_ancla_con_fragmento_codificado_resuelve(self):
        """Evita falsos positivos en anclas Unicode codificadas."""
        self.escribir("index.html", self.html())  # destino del enlace de navegacion href="/"
        ruta = self.pagina(
            body=(
                '<h2 id="año">Seccion</h2>'
                '<a href="#a%C3%B1o">Ir a seccion</a>'
            )
        )

        fallos = qc.c_enlaces(self.contexto(ruta))

        self.assertEqual(fallos, [])

    # BUG: existe() permite resolver rutas con .. fuera de ROOT.
    # Puede dar por validos recursos ajenos al repositorio auditado.
    # Arreglo minimo: resolver la ruta y exigir que permanezca bajo ROOT
    # mediante Path.is_relative_to() tras normalizar ambos caminos.
    def test_existe_no_escapa_del_directorio_raiz(self):
        """Evita validar recursos externos al arbol auditado."""
        exterior = self.root.parent / (
            self.root.name + "-recurso-externo.txt"
        )
        exterior.write_text("externo", encoding="utf-8")
        self.addCleanup(exterior.unlink, missing_ok=True)

        href = "/../" + exterior.name

        self.assertFalse(qc.existe(self.root, href))

    def test_landmarks_detecta_main_duplicado(self):
        """Evita aceptar paginas con dos regiones principales."""
        ruta = self.pagina(
            body='<main><p>Segunda region principal</p></main>'
        )

        fallos = qc.c_landmarks(self.contexto(ruta))

        self.assertTrue(
            any("main" in causa for causa, _ in fallos)
        )

    # BUG: <main role="main"> se cuenta dos veces como dos landmarks.
    # Esto genera falsos positivos en HTML semanticamente correcto.
    # Arreglo minimo: contar elementos principales distintos en lugar
    # de sumar etiquetas y roles del mismo elemento.
    def test_main_con_role_main_no_cuenta_doble(self):
        """Evita falsos positivos en main con rol ARIA explicito."""
        ruta = self.escribir(
            "editoriales/ejemplo/index.html",
            self.html().replace(
                '<main id="contenido">',
                '<main id="contenido" role="main">',
            ),
        )

        fallos = qc.c_landmarks(self.contexto(ruta))

        self.assertEqual(fallos, [])

    def test_ids_duplicados_agrupados(self):
        """Evita multiplicar incidencias por un mismo ID duplicado."""
        ruta = self.pagina(
            body=(
                '<section id="duplicado"></section>'
                '<section id="duplicado"></section>'
                '<section id="duplicado"></section>'
            )
        )

        fallos = qc.c_ids_unicos(self.contexto(ruta))

        self.assertEqual(len(fallos), 1)
        self.assertIn("duplicado", fallos[0][1])

    def test_encabezados_detecta_salto_h1_h3(self):
        """Evita aceptar jerarquias de encabezados discontinuas."""
        ruta = self.pagina(
            body='<h3>Subseccion sin h2</h3>'
        )

        fallos = qc.c_encabezados(self.contexto(ruta))

        self.assertTrue(fallos)
        self.assertIn("h1->h3", fallos[0][1])

    def test_sitemap_reconoce_varios_ficheros(self):
        """Evita perder paginas repartidas entre varios sitemaps."""
        a = self.pagina("editoriales/a/index.html")
        b = self.pagina("editoriales/b/index.html")

        self.sitemap(
            [qc.url_de(self.root, a)],
            "sitemap.xml",
        )
        self.sitemap(
            [qc.url_de(self.root, b)],
            "reading-sitemap.xml",
        )

        paginas = qc.paginas_del_sitio(self.root)

        self.assertCountEqual(
            paginas["editoriales"],
            [a, b],
        )

    # BUG: sitemap_urls usa una expresion regular que exige <loc> sin
    # prefijo de namespace ni atributos y no decodifica entidades XML.
    # Puede omitir paginas publicadas en sitemaps XML validos.
    # Arreglo minimo: utilizar xml.etree.ElementTree y reconocer
    # elementos loc independientemente del prefijo de namespace.
    def test_sitemap_xml_con_namespace_prefijado(self):
        """Evita perder URLs de sitemaps XML validos con prefijos."""
        ruta = self.pagina("editoriales/a/index.html")
        url = qc.url_de(self.root, ruta)

        self.escribir(
            "sitemap.xml",
            (
                '<s:urlset xmlns:s="'
                'http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<s:url><s:loc>'
                + url
                + '</s:loc></s:url></s:urlset>'
            ),
        )

        self.assertIn(
            url.rstrip("/"),
            qc.sitemap_urls(self.root),
        )

    # BUG: paginas_del_sitio acepta URLs de otros dominios cuando
    # su ruta coincide con un archivo HTML local.
    # Puede incorporar entradas ajenas al inventario del sitio.
    # Arreglo minimo: comprobar scheme y netloc con urlsplit()
    # frente a SITE antes de convertir la URL en ruta local.
    def test_sitemap_ajeno_no_incluye_archivos_locales(self):
        """Evita auditar como propias URLs de dominios externos."""
        self.pagina("editoriales/a/index.html")

        self.sitemap([
            "https://dominio-ajeno.example/editoriales/a/"
        ])

        paginas = qc.paginas_del_sitio(self.root)

        self.assertEqual(paginas, {})

    def test_correr_agrupa_misma_causa_en_varias_paginas(self):
        """Evita crear una incidencia independiente por cada ficha."""
        rutas = [
            self.pagina(f"editoriales/ficha-{i}/index.html")
            for i in range(12)
        ]

        resultado = self.correr(
            rutas,
            contratos=[
                ("seo-canonical", "canonical", qc.c_canonical)
            ],
        )

        self.assertEqual(resultado["paginas"], 12)
        self.assertEqual(resultado["fallos_brutos"], 12)
        self.assertEqual(resultado["fallos_unicos"], 1)

        grupo = resultado["grupos"][0]

        self.assertEqual(grupo["paginas"], 12)
        self.assertEqual(len(grupo["urls"]), 12)
        self.assertLessEqual(len(grupo["ejemplos"]), 3)

    def test_correr_no_confunde_aserciones_con_tests(self):
        """Evita inflar las metricas de tests generados con aserciones."""
        rutas = [
            self.pagina(f"editoriales/p-{i}/index.html")
            for i in range(4)
        ]

        contratos = [
            ("titulo", "titulo", qc.c_title),
            ("h1", "encabezado", qc.c_h1),
            ("ids", "identificadores", qc.c_ids_unicos),
        ]

        resultado = self.correr(rutas, contratos=contratos)

        self.assertEqual(resultado["paginas"], 4)
        self.assertEqual(resultado["aserciones"], 12)
        self.assertEqual(resultado["fallos_brutos"], 0)
        self.assertEqual(resultado["fallos_unicos"], 0)

    def test_ejecutar_sitio_solo_audita_paginas_existentes(self):
        """Evita que entradas obsoletas del sitemap aborten el lote."""
        existente = self.pagina("editoriales/existente/index.html")

        self.sitemap([
            qc.url_de(self.root, existente),
            "https://davidportodiaz.com/editoriales/borrada/",
        ])

        resultado = qc.ejecutar_sitio(
            self.root,
            contratos=[
                ("h1", "encabezado", qc.c_h1)
            ],
        )

        self.assertEqual(resultado["paginas"], 1)
        self.assertEqual(resultado["familias"]["editoriales"], 1)

    # BUG: homogeneidad() accede a most_common(1)[0] cuando una
    # familia no tiene paginas, provocando IndexError.
    # Una familia temporalmente vacia no debe detener el lote.
    # Arreglo minimo: omitir familias vacias antes de calcular la moda.
    def test_homogeneidad_acepta_familia_vacia(self):
        """Evita que una familia sin fichas detenga una ejecucion."""
        resultado = qc.homogeneidad({
            "editoriales": [],
        })

        self.assertEqual(resultado, [])

    def test_homogeneidad_detecta_plantilla_minoritaria(self):
        """Evita que una ficha estructuralmente distinta pase inadvertida."""
        rutas = []

        for i in range(9):
            body = (
                '<h2>Seccion comun</h2>'
                if i < 8
                else '<h3>Seccion distinta</h3>'
            )
            rutas.append(
                self.pagina(
                    f"editoriales/ficha-{i}/index.html",
                    body=body,
                )
            )

        paginas = {
            "editoriales": [
                self.contexto(ruta)
                for ruta in rutas
            ]
        }

        fallos = qc.homogeneidad(paginas)

        self.assertEqual(len(fallos), 1)
        self.assertEqual(
            fallos[0][1]["ruta"],
            rutas[-1],
        )

    def test_rendimiento_agrupacion_miles_de_paginas(self):
        """Evita crecimiento desproporcionado al agrupar miles de fallos."""
        rutas = [
            self.root / "editoriales" / f"ficha-{i}" / "index.html"
            for i in range(2000)
        ]

        pagina = qc.Pagina()
        pagina.feed(self.html())

        def lectura_simulada(root, ruta):
            return pagina

        inicio = time.monotonic()

        with patch.object(qc, "leer", side_effect=lectura_simulada):
            with patch.object(qc, "sitemap_urls", return_value=set()):
                resultado = self.correr(
                    rutas,
                    contratos=[
                        ("canonical", "canonical", qc.c_canonical)
                    ],
                )

        duracion = time.monotonic() - inicio

        self.assertEqual(resultado["paginas"], 2000)
        self.assertEqual(resultado["fallos_brutos"], 2000)
        self.assertEqual(resultado["fallos_unicos"], 1)
        self.assertEqual(resultado["grupos"][0]["paginas"], 2000)
        self.assertLess(duracion, 10.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
