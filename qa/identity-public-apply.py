#!/usr/bin/env python3
"""Deterministic, idempotent migration for the public Identity family.

This script deliberately touches only autor.html, prensa.html, premios.html and
 eventos.html. It fails loudly when the expected baseline shape is not found,
so a concurrent edit cannot be silently overwritten.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["autor.html", "prensa.html", "premios.html", "eventos.html"]
IDENTITY_LINK = '  <link rel="stylesheet" href="/assets/v1-identity.css" />'
FAMILIES_LINK = '  <link rel="stylesheet" href="/assets/v1-families.css" />'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        if new in text:
            return text
        raise RuntimeError(f"{label}: baseline fragment not found")
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 baseline fragment, found {count}")
    return text.replace(old, new, 1)


def add_identity_css(text: str, page: str) -> str:
    if IDENTITY_LINK in text:
        return text
    return replace_once(
        text,
        FAMILIES_LINK,
        FAMILIES_LINK + "\n" + IDENTITY_LINK,
        f"{page}: identity stylesheet",
    )


def update_autor(text: str) -> str:
    # No biography/metadata rewrite: the current factual content is preserved.
    return add_identity_css(text, "autor.html")


def update_prensa(text: str) -> str:
    text = add_identity_css(text, "prensa.html")

    # Copy feedback is already visual. aria-live makes that same state change
    # announced to assistive technology without adding a modal or extra layout.
    marker = 'class="copy-btn" data-copy-target='
    if marker in text:
        text = text.replace(marker, 'class="copy-btn" aria-live="polite" data-copy-target=')
    elif 'class="copy-btn" aria-live="polite" data-copy-target=' not in text:
        raise RuntimeError("prensa.html: copy controls not found")

    # A public 1024px cover link already exists immediately above this note.
    # Do not call the same asset both public and 'under request'.
    old = (
        'Portada en alta resolución bajo petición:<br><a href="mailto:'
        'samuelentremundos@gmail.com?subject=Portada%20Las%20manecillas%20del%20recuerdo">'
        'samuelentremundos&#64;gmail.com</a>'
    )
    new = (
        'La portada enlazada arriba está disponible públicamente. Para otras versiones o '
        'consultar condiciones de uso:<br><a href="mailto:'
        'samuelentremundos@gmail.com?subject=Portada%20Las%20manecillas%20del%20recuerdo">'
        'samuelentremundos&#64;gmail.com</a>'
    )
    text = replace_once(text, old, new, "prensa.html: Manecillas cover state")
    return text


def update_premios(text: str) -> str:
    text = add_identity_css(text, "premios.html")

    # Antología = trayectoria/publicación, not an award.
    anthology_award = (
        ',\n          "Seleccionado en antología La memoria de las tierras del norte — '
        'Diversidad Literaria (2026)"'
    )
    if anthology_award in text:
        text = text.replace(anthology_award, "", 1)
    elif '"award": [' in text and "Seleccionado en antología" in text.split('"award": [', 1)[1].split(']', 1)[0]:
        raise RuntimeError("premios.html: unexpected anthology award shape")

    # Debut is a publication milestone. Move it out of the award ledger while
    # retaining the content and internal link.
    debut_pattern = re.compile(
        r'\n        <li>\n          <span>2025</span>\n          <div>\n'
        r'            <h3>Debut novelístico publicado</h3>.*?\n        </li>',
        re.S,
    )
    m = debut_pattern.search(text)
    debut_block = m.group(0) if m else None
    if debut_block:
        text = text[:m.start()] + text[m.end():]
    elif "Debut novelístico publicado" not in text:
        # already migrated: rebuilt block below will exist in trajectory
        debut_block = None
    else:
        raise RuntimeError("premios.html: debut milestone could not be isolated")

    old_head = (
        '<section class="v1-section" id="colaboraciones">\n'
        '      <div class="v1-section__head"><p class="eyebrow">Obra y trayectoria</p>'
        '<h2>Colaboraciones y proyectos literarios.</h2></div>\n'
        '      <ol class="awards-ledger">'
    )
    new_head = (
        '<section class="v1-section" id="colaboraciones">\n'
        '      <div class="v1-section__head"><p class="eyebrow">Trayectoria</p>'
        '<h2>Publicaciones y colaboraciones.</h2></div>\n'
        '      <ol class="awards-ledger">'
    )
    if old_head in text:
        text = text.replace(old_head, new_head, 1)
    elif new_head not in text:
        raise RuntimeError("premios.html: trajectory section head not found")

    if debut_block and "Debut novelístico publicado" not in text:
        text = text.replace(new_head, new_head + debut_block, 1)

    # Reader reviews are reception, not trajectory and not awards. Preserve the
    # existing quotes/link but give them a semantically honest home.
    review_pattern = re.compile(
        r'\n        <li>\n          <span>Lectores</span>\n          <div>\n'
        r'            <h3>Reseñas de lectores</h3>.*?\n        </li>',
        re.S,
    )
    rm = review_pattern.search(text)
    review_block = rm.group(0) if rm else None
    if review_block:
        text = text[:rm.start()] + text[rm.end():]
    elif 'id="recepcion"' not in text and "Reseñas de lectores" in text:
        raise RuntimeError("premios.html: reader reception block could not be isolated")

    if review_block and 'id="recepcion"' not in text:
        reception = (
            '\n\n    <section class="v1-section" id="recepcion">\n'
            '      <div class="v1-section__head"><p class="eyebrow">Recepción</p>'
            '<h2>Lectores y obra.</h2></div>\n'
            '      <ol class="awards-ledger awards-ledger--reception">'
            + review_block +
            '\n      </ol>\n'
            '    </section>'
        )
        anchor = '\n\n    <section class="v1-section" id="conocer">'
        text = replace_once(text, anchor, reception + anchor, "premios.html: reception section")

    return text


def update_eventos(text: str) -> str:
    text = add_identity_css(text, "eventos.html")

    # Aranjuez has no event photograph in assets/eventos. A generic author OG
    # image is not documentary evidence of this event.
    generic_image = (
        '        "image": "https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp",\n'
    )
    if generic_image in text:
        text = text.replace(generic_image, "", 1)

    # Avoid a false organizer link that points back to our own event anchor.
    old_org = (
        '        "organizer": { "@type": "Organization", "name": "Ayuntamiento de Aranjuez", '
        '"url": "https://davidportodiaz.com/eventos.html#feria-libro-aranjuez-2026" },'
    )
    new_org = '        "organizer": { "@type": "Organization", "name": "Ayuntamiento de Aranjuez" },'
    if old_org in text:
        text = text.replace(old_org, new_org, 1)
    elif new_org not in text:
        raise RuntimeError("eventos.html: Aranjuez organizer shape not found")

    # Replace the two temporal sections as one unit. This keeps the only two
    # events explicitly authorized for this task, puts future state first and
    # removes unsourced January entries / a book publication masquerading as an event.
    sections = re.compile(
        r'    <section class="v1-section" id="proximos">.*?'
        r'    </section>\n\n'
        r'    <section class="v1-section" id="pasados">.*?'
        r'    </section>',
        re.S,
    )

    new_sections = '''    <section class="v1-section" id="proximos">
      <div class="v1-section__head"><p class="eyebrow">Agenda</p><h2>Próximas fechas.</h2></div>
      <div class="event-year">
        <h3>Ahora</h3>
        <div class="event-empty">
          <h3 class="event-empty__title">Ahora mismo no hay una próxima fecha publicada.</h3>
          <p>La agenda se actualiza únicamente cuando una firma, presentación o encuentro está confirmado.</p>
          <div class="v1-masthead__actions event-empty__actions">
            <a class="primary-action" href="mailto:samuelentremundos@gmail.com?subject=Solicitud%20de%20presentaci%C3%B3n%20%E2%80%94%20David%20Porto%20D%C3%ADaz">Solicitar presentación</a>
            <a class="text-action" href="#pasados">Ver archivo reciente</a>
          </div>
        </div>
      </div>
    </section>

    <section class="v1-section" id="pasados">
      <div class="v1-section__head"><p class="eyebrow">Archivo</p><h2>Eventos recientes.</h2></div>
      <div class="event-year">
        <h3>2026</h3>
        <ol class="event-list">
          <li class="event-entry" id="feria-libro-madrid-2026">
            <time datetime="2026-06-10">10 jun 2026</time>
            <div>
              <figure>
                <img src="/assets/eventos/david-porto-diaz-feria-libro-madrid-2026-caseta-337.webp" alt="David Porto Díaz en la caseta 337 de la Feria del Libro de Madrid 2026" width="1500" height="2000" loading="lazy" decoding="async" />
                <figcaption>Firma de <em>Samuel entre mundos</em> en la Feria del Libro de Madrid 2026 · Caseta 337</figcaption>
              </figure>
              <h3>Feria del Libro de Madrid</h3>
              <p>David Porto Díaz firmó ejemplares de <em>Samuel entre mundos</em> en la Feria del Libro de Madrid 2026. Horario: 19:00–20:00. Caseta 337.</p>
              <a class="text-action" href="/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/">Ver crónica y fotos</a>
            </div>
          </li>
          <li class="event-entry" id="feria-libro-aranjuez-2026">
            <time datetime="2026-05-23">23 may 2026</time>
            <div>
              <h3>Feria del Libro de Aranjuez</h3>
              <p>Firma de <em>Samuel entre mundos</em> en la Plaza de la Constitución, Aranjuez. Organizó el Ayuntamiento de Aranjuez. Acceso libre y gratuito.</p>
              <a class="text-action" href="/ferias.html#aranjuez">Ver documentación del evento</a>
            </div>
          </li>
        </ol>
      </div>
    </section>'''

    m = sections.search(text)
    if m:
        text = text[:m.start()] + new_sections + text[m.end():]
    elif 'Ahora mismo no hay una próxima fecha publicada.' not in text:
        raise RuntimeError("eventos.html: temporal sections not found")
    return text


def validate_output(files: dict[str, str]) -> None:
    for page, text in files.items():
        if text.count(IDENTITY_LINK) != 1:
            raise RuntimeError(f"{page}: identity stylesheet count != 1")
        if 'data-family="identity"' not in text:
            raise RuntimeError(f"{page}: identity family marker missing")

    premios = files["premios.html"]
    award_region = premios.split('"award": [', 1)[1].split(']', 1)[0]
    if "antología" in award_region.lower():
        raise RuntimeError("premios.html: anthology still classified as award")
    if premios.split('id="reconocimientos"', 1)[1].split('</section>', 1)[0].find("Debut novelístico publicado") != -1:
        raise RuntimeError("premios.html: publication still inside awards section")
    if 'id="recepcion"' not in premios:
        raise RuntimeError("premios.html: reception section missing")

    eventos = files["eventos.html"]
    if eventos.find('id="proximos"') > eventos.find('id="pasados"'):
        raise RuntimeError("eventos.html: upcoming state does not precede archive")
    for forbidden in ("Presentación en La Vecinal", "Presentación oficial de Samuel entre mundos", "Publicación de Samuel entre mundos"):
        if forbidden in eventos:
            raise RuntimeError(f"eventos.html: unverified entry still visible: {forbidden}")
    if eventos.count('https://schema.org/EventCompleted') != 2:
        raise RuntimeError("eventos.html: expected exactly two completed event schemas")
    aranjuez_schema = eventos.split('eventos.html#feria-libro-aranjuez-2026', 1)[1].split('\n      }', 1)[0]
    if "david-porto-imagen-compartir.webp" in aranjuez_schema:
        raise RuntimeError("eventos.html: generic image still attached to Aranjuez schema")

    prensa = files["prensa.html"]
    if prensa.count('class="copy-btn" aria-live="polite"') < 4:
        raise RuntimeError("prensa.html: copy buttons are not all live-announced")
    if "Portada en alta resolución bajo petición" in prensa.split('id="ficha-manecillas"', 1)[1].split('</section>', 1)[0]:
        raise RuntimeError("prensa.html: Manecillas cover availability contradiction remains")


def main() -> None:
    files: dict[str, str] = {}
    updaters = {
        "autor.html": update_autor,
        "prensa.html": update_prensa,
        "premios.html": update_premios,
        "eventos.html": update_eventos,
    }
    for page in PAGES:
        path = ROOT / page
        original = path.read_text(encoding="utf-8")
        updated = updaters[page](original)
        files[page] = updated

    validate_output(files)
    for page, updated in files.items():
        (ROOT / page).write_text(updated, encoding="utf-8")

    print(json.dumps({"updated": PAGES, "status": "ok"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
