#!/usr/bin/env python3
"""Genera una narración de la descripción original; nunca descarga capítulos ajenos.

Herramienta editorial opcional: requiere edge-tts en el entorno de generación.
El MP3 versionado se sirve estáticamente; los visitantes no llaman al proveedor.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', required=True)
    parser.add_argument('--voice', default='es-ES-ElviraNeural')
    args=parser.parse_args()
    data=json.loads((ROOT/'data/reading-catalogue.json').read_text(encoding='utf-8'))
    book=next(b for b in data['libros'] if b['slug']==args.book)
    if book.get('descripcion_original_confirmada') is not True:
        parser.error('Solo se narra una descripción original confirmada')
    digest=hashlib.sha256((args.voice+'|-4%|'+book['descripcion_breve']).encode()).hexdigest()[:12]
    rel=f'/assets/reading-audio/{book["slug"]}-{digest}.mp3'
    target=ROOT/rel.lstrip('/')
    if not target.exists():
        import edge_tts
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix('.tmp.mp3')
        try:
            asyncio.run(edge_tts.Communicate(book['descripcion_breve'],args.voice,rate='-4%').save(str(temporary)))
            if temporary.stat().st_size < 1000:
                raise ValueError('Audio vacío')
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise SystemExit('No se pudo generar el audio con el proveedor. Se mantiene la lectura del navegador y no se publica un MP3 incompleto.')
    reviewpath=ROOT/'data/reading-import-review.json'
    review=json.loads(reviewpath.read_text(encoding='utf-8'))
    item=next(r for r in review['reviews'].values() if r.get('portada_local')==book['portada_local'])
    item['audio_descripcion']=rel
    item['audio_voz']='Voz sintética · '+('Elvira (español de España)' if args.voice=='es-ES-ElviraNeural' else args.voice)
    reviewpath.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Audio generado: {rel} ({target.stat().st_size} bytes)')


if __name__=='__main__':
    main()
