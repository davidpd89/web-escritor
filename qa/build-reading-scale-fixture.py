"""Synthetic 100/200-book fixtures, isolated from all public artefacts."""
import base64
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scale_builder',ROOT/'scripts/build-reading-catalogue.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
data=json.loads((ROOT/'data/reading-catalogue.json').read_text(encoding='utf-8'))
template=(ROOT/'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
seed=data['libros'][0]
data['libros']=[]
data['libro_categorias']=[]
output={'catalogues':{}}
with tempfile.TemporaryDirectory(prefix='reading-scale-') as directory:
    root=Path(directory)
    covers=root/'assets/reading-covers'
    covers.mkdir(parents=True)
    for i in range(200):
        stem='9780000'+str(i).zfill(5)
        isbn=stem+str(-sum(int(c)*(1 if n%2==0 else 3) for n,c in enumerate(stem))%10)
        image=Image.new('RGB',(120,180),(i,30,90))
        filename='qa-reading-'+str(i)+'.png'
        image.save(covers/filename)
        book={k:v for k,v in copy.deepcopy(seed).items() if k in {
            'estado','descripcion_original_confirmada','portada_edicion_verificada','autorizacion_o_base_uso',
            'portada_fecha_revision','fecha_verificacion','fecha_actualizacion','edicion'}}
        book.update(id='qa-book-'+str(i),slug='qa-book-'+str(i),titulo='Prueba técnica '+str(i).zfill(3),
                    autores=['Autor técnico '+str(i%7)],isbn13=isbn,
                    descripcion_breve='Descripción técnica original del libro de prueba número '+str(i)+', únicamente para el entorno aislado de QA.',
                    portada_local='/assets/reading-covers/'+filename,portada_ancho=120,portada_alto=180,
                    portada_fuente_url='https://fuente.invalid/cover/'+str(i),fuente_bibliografica_url='https://fuente.invalid/book/'+str(i),
                    fuente_publicacion_url='https://fuente.invalid/book/'+str(i),editorial='Editorial de QA',
                    fecha_publicacion=['2026-10-21','2026-10-07','2026-10-06','2026-10-05','2026-09-21'][i%5],
                    formato_edicion='tapa-blanda',amazon_busqueda_isbn='https://www.amazon.es/s?k='+isbn+'&tag=contrato-21')
        if i%10==9:
            book['fecha_publicacion']='1990-01-01'
        if i%5!=4:
            book['numero_paginas']=[120,240,450,700][i%5]
        data['libros'].append(book)
        cats=['fantasia' if i%2==0 else 'cocina','adultos']
        if i%4==0:
            cats+=['halloween']
        if i%10==9:
            cats+=['clasicos']
        data['libro_categorias'] += [{'libro_id':book['id'],'categoria_id':c} for c in cats]
    for count in [100,200]:
        selected=copy.deepcopy(data)
        selected['libros']=selected['libros'][:count]
        selected_ids={b['id'] for b in selected['libros']}
        selected['libro_categorias']=[r for r in selected['libro_categorias'] if r['libro_id'] in selected_ids]
        builder.validate(selected,root)
        output['catalogues'][str(count)]={'html':builder.render_hub(selected,selected['libros'],template),'books':selected['libros']}
    output['cover']=base64.b64encode((covers/'qa-reading-0.png').read_bytes()).decode()
destination=Path(sys.argv[1])
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(output,ensure_ascii=False),encoding='utf-8')
print('PASS: 100/200 editions, unique validated ISBNs, covers and relationships; no public fixture files.')
