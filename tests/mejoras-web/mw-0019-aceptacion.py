from pathlib import Path


SOURCE = Path('assets/v1-home-editorial-v3.js')
READER_URL = '/lectores-beta/'
AUTHOR_URL = '/lectores-beta/enviar-manuscrito/'


def test_home_beta_links():
    source = SOURCE.read_text(encoding='utf-8')

    # Comunidad: lectores potenciales, no autores.
    reader_card = (
        "['Comunidad', 'Lectores beta', "
        "'Sé el primero en leer contenido y opina antes de que llegue a todos.', "
        f"'{READER_URL}']"
    )
    assert source.count(reader_card) == 1, (
        'La tarjeta Comunidad > Lectores beta debe enlazar a la página general.'
    )

    # Herramientas gratuitas: envío de manuscritos.
    tools_card = (
        "['Lectores beta', "
        "'Tengo un manuscrito y me gustarían opiniones de lectores beta', "
        "'Un punto de entrada para autores que buscan primeras lecturas antes de mover el texto.', "
        f"'{AUTHOR_URL}', 'yale-tile--blue']"
    )
    assert source.count(tools_card) == 1, (
        'La tarjeta de autores en Herramientas debe enlazar al envío de manuscritos.'
    )

    # Leer y recursos: segundo acceso para autores.
    reading_card = (
        "['Herramientas', 'Tengo un manuscrito y quiero opiniones', "
        "'Acceso para autores que buscan lectores beta antes de mover su texto.', "
        f"'{AUTHOR_URL}']"
    )
    assert source.count(reading_card) == 1, (
        'La tarjeta de autores en Leer y recursos debe enlazar al envío de manuscritos.'
    )

    # Exactamente los tres destinos previstos en el archivo.
    assert source.count(f"'{READER_URL}'") == 1
    assert source.count(f"'{AUTHOR_URL}'") == 2

    # Los fragmentos inexistentes no deben reaparecer.
    assert '#quiero-ser-lector' not in source
    assert '#enviar-manuscrito' not in source

    # Ambas rutas deben corresponder a páginas reales del repositorio.
    assert Path('lectores-beta/index.html').is_file(), (
        'No existe la página general del programa de lectores beta.'
    )
    assert Path('lectores-beta/enviar-manuscrito/index.html').is_file(), (
        'No existe la página de envío de manuscritos.'
    )


if __name__ == '__main__':
    test_home_beta_links()
    print('MW-0019: aceptación correcta')
