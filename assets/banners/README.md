# Home banners

Los banners `imageOnly` de la Home usan art direction por dispositivo. No se
debe intentar resolver el encuadre con `object-position` cuando una misma
imagen no funciona en escritorio y movil.

Contrato activo:

- Desktop/tablet: `<base>-desktop.<ext>`, normalmente 2400 x 600 px, 4:1.
- Mobile: `<base>-mobile.<ext>`, normalmente 1200 x 675 px, 16:9.
- Fallback: `<base>-final.<ext>` o el banner antiguo definido en JS.

El JS asigna estas variables CSS al crear cada banner:

- `--feature-banner-desktop-image`
- `--feature-banner-mobile-image`

El CSS comun esta en `assets/v1-banner-art-direction-v5.css`.

Regla visual:

- Desktop debe tener mucho fondo a izquierda y derecha.
- Los objetos importantes deben quedar completos en el 40 % central.
- Mobile debe estar recompuesto, no recortado desde desktop.
- No incrustar titulos ni subtitulos en la imagen.
- Si el libro, reloj, cara u objeto principal se corta, hay que regenerar el
  asset desktop/mobile, no tocar el `object-position`.

Assets activos:

- `manecillas-home-banner-desktop.png`
- `manecillas-home-banner-mobile.png`
- `samuel-home-banner-desktop.png`
- `samuel-home-banner-mobile.png`

Origen local de trabajo indicado por David:

`C:\GIT\web-escritor\WEB DAVID PORTO nuevas ideas\DISEÑO Y DEMÁS\Imagenes generadas para implementar`
