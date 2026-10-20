"""Optional fixed Elvira narration of our own bibliographic text, cached by hash."""
import asyncio
import hashlib
from pathlib import Path

VOICE = 'es-ES-ElviraNeural'


def narrate(book, root):
    if book.get('descripcion_original_confirmada') is not True:
        raise ValueError('Solo se narra texto propio confirmado')
    text = book['descripcion_breve']
    digest = hashlib.sha256((VOICE + '|-4%|' + text).encode()).hexdigest()[:12]
    relative = '/assets/reading-audio/' + book['slug'] + '-' + digest + '.mp3'
    target = Path(root) / relative.lstrip('/')
    if not target.exists():
        import edge_tts
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp.mp3')
        async def generate():
            await asyncio.wait_for(edge_tts.Communicate(text, VOICE, rate='-4%').save(str(temporary)), timeout=45)
        try:
            asyncio.run(generate())
            if temporary.stat().st_size < 1000:
                raise ValueError('Narración vacía')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    book['audio_descripcion'] = relative
    book['audio_voz'] = 'Elvira (español de España)'
    return relative
