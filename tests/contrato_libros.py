"""Canal estructurado entre los contratos de datos y la cuarentena de la carga (Fable R4-2b).

Un contrato que recorre libros declara qué libros incumplen qué regla con `incumplen(regla, {id: motivo})`. La
puerta (scripts/check-reading-data.py) guarda esos pares en su JSON de fallos y la carga aparta exactamente esos
libros, sin buscar ids con expresiones regulares en el texto del fallo: el texto puede citar a un vecino (libros
relacionados), un título o una URL, y entonces se apartaba el libro equivocado o se paraba el lote entero.

Los contratos en script (tests/test-*.py) no pasan por unittest: la puerta les pone `CONTRATO_LIBROS_FICHERO` y
`incumplen` deja ahí los mismos pares antes de fallar, para que también ellos nombren a sus libros.
"""
import json
import os


class Incumplen(AssertionError):
    """Fallo de un contrato con los libros que lo incumplen: {id del libro: motivo}."""

    def __init__(self, regla, libros):
        self.regla = regla
        self.libros = {str(k): str(v) for k, v in libros.items()}
        muestra = '; '.join(f'{k}: {v}' for k, v in list(self.libros.items())[:20])
        resto = len(self.libros) - 20
        super().__init__(f'{regla} ({len(self.libros)} libros): {muestra}' + (f'; y {resto} más' if resto > 0 else ''))


def incumplen(regla, libros):
    """Falla con los libros que incumplen `regla` ({id: motivo}); no hace nada si no hay ninguno."""
    libros = dict(libros)
    if libros:
        error = Incumplen(regla, libros)
        destino = os.environ.get('CONTRATO_LIBROS_FICHERO')
        if destino:
            with open(destino, 'w', encoding='utf-8') as fh:
                json.dump({'regla': error.regla, 'libros': error.libros}, fh, ensure_ascii=False)
        raise error
