# Investigación GPT — UX y contrato de datos (22/10/2026)

**PR hija de #699.** Rama basada en research/gpt-social-dashboard-2026-10-22. Solo análisis y código de referencia, no instalado ni ejecutado; sin Actions ni merge.

## Alcance cerrado
- Proponer el futuro /redes-sociales/ sin tocar aún el sitio. Enlaces y marcas actuales se encuentran en autor.html, scripts/build-site-shell.py y data/navigation.json; no duplicarlos a mano.
- Hero editorial, 3 cifras como máximo con cobertura y periodo, tarjetas de redes con SVG locales, microcopy y CTA de contacto/press-kit.
- «Seguir» es un enlace al perfil externo, no una acción API de follow del visitante. Respetar accesibilidad y perfiles vacíos.
- Compartir contrato: id, profile_url, source, observed_at, followers, views_30d, impressions_30d, interactions_30d, status.
- Si la suma es incompleta, NO titular «total global» sin aclarar «redes con datos». Impresiones no son alcance; no sumar views con impressions.

## Prototipo reutilizable en Python estándar (autoría propia; NO integrado)
~~~python
def count_or_none(value):
    if type(value) is not int or value < 0:
        return None
    return value

def total_followers(networks):
    values = [count_or_none(item.get("followers")) for item in networks]
    known = [n for n in values if n is not None]
    return {"value": sum(known) if known else None,
            "coverage": len(known), "eligible": len(networks)}
~~~
Este código evita el error Python de bool siendo int, y diferencia «sin dato» de cero.

## Assets reutilizables
[Simple Icons CC0](https://github.com/simple-icons/simple-icons) (revisar marcas y DISCLAIMER); [Lucide ISC](https://github.com/lucide-icons/lucide) para iconos genéricos. Copia de SVGs locales con procedencia/versión, no dependencia CDN.
## Integración futura
Crear registro canónico y validador, HTML estático, CSS con tokens actuales, JS de mejora progresiva. Modificar shell builder, navegación, sitemap, metadata social, schema.org, privacidad y taxonomy solo con pruebas.
## QA pendiente
0/null/bool/floats, marca sin métricas, timestamps caducados, total de 0 redes, overflow 320px, navegador sin JS, teclado/AA, enlaces externos y regresión de navegación. No hay código aplicado.

## Entrega Claude
Releer fuente oficial y estado main, integrar una sola vez sobre el contrato padre, ejecutar pruebas offline/live autorizadas, documentar limitaciones reales antes de solicitar merge. Se mantiene aislamiento respecto de las demás hijas.
