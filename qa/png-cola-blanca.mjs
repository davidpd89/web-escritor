// Una captura fullPage mide el alto, la página encoge al redimensionar y el resto se rellena de blanco puro.
// El tamaño de ese relleno depende del momento (12 de 24 baselines lo tienen, de 0 a ~180 px), así que no es
// contenido: se recorta en ambas imágenes antes de comparar. Si el contenido cambia de alto, el pie acaba en
// otra fila y la comparación sigue fallando.
export function trimWhiteTail(png) {
  const rowBytes = png.width * 4;
  let height = png.height;
  while (height > 1) {
    const start = (height - 1) * rowBytes;
    let white = true;
    for (let i = start; i < start + rowBytes; i += 1) {
      if (png.data[i] !== 255) { white = false; break; }
    }
    if (!white) break;
    height -= 1;
  }
  if (height === png.height) return png;
  return { width: png.width, height, data: png.data.subarray(0, height * rowBytes) };
}
