# Tracking — Pinterest Business + dominio

**Revisión:** 2026-09-08

**Estado:** `RESEARCHED · FREE_BUSINESS_CONFIRMED · DOMAIN_CLAIM_FREE · PUBLIC_PROFILE_NOT_OBSERVED · READY_FOR_AUTHENTICATED_PILOT`

## Objetivo

Evaluar Pinterest como canal visual evergreen de descubrimiento para libros, universo y contenido útil del Cuaderno, usando exclusivamente cuenta Business gratuita y reclamación gratuita de `davidportodiaz.com`.

No se contemplan Pinterest Ads ni catálogos/comercio que requieran trabajo adicional sin señal de tráfico.

## Por qué sí merece un piloto

A diferencia de una red que solo añade otro perfil, Pinterest ofrece dos activos concretos y medibles sin coste:

1. **Business Analytics** para medir impresiones, guardados y rendimiento de Pins.
2. **Website claim**: al reclamar el dominio, Pinterest asocia al perfil los Pins creados desde contenido guardado de la web y permite medir cómo se comparte ese contenido.

Esto puede aportar descubrimiento evergreen y referrals hacia artículos, herramientas y páginas de libros. El valor es secundario frente a Google/Goodreads/bibliotecas, así que debe probarse con un piloto pequeño, no convertirse en una obligación editorial diaria.

## Estado observado

- No aparece actualmente `pinterest.com` en el repo `main`.
- La búsqueda pública por `David Porto Díaz` no ha localizado un perfil Pinterest inequívoco.
- Estado correcto: `PUBLIC_PROFILE_NOT_OBSERVED`, no `ABSENT`.

Claude debe comprobar primero si existe una cuenta personal/business previa antes de crear otra.

## Modelo oficial actual

Pinterest confirma:

- las cuentas Business son gratuitas;
- una cuenta Business da acceso a Business Hub y Pinterest Analytics;
- una web puede ser reclamada gratuitamente si se posee/controla el dominio y se puede editar su código/DNS;
- una web solo puede estar reclamada por una cuenta Pinterest a la vez;
- métodos actuales de verificación:
  - conexión con Google Merchant Center en algunas cuentas;
  - HTML tag;
  - HTML file;
  - DNS TXT;
- tras verificar, Pinterest indica que el tag/archivo/TXT puede retirarse;
- reclamar la web hace que contenido guardado desde ella se asocie al perfil y aporta datos de compartición.

Fuentes oficiales:

- https://help.pinterest.com/en/business/article/get-a-business-account
- https://help.pinterest.com/en/business/article/claim-your-website

## Identidad canónica

- Nombre: `David Porto Díaz`
- Web: https://davidportodiaz.com/
- Autor principal de `Las manecillas del recuerdo` y `Samuel entre mundos`.

No usar Pinterest como autoridad bibliográfica para corregir ISBN, páginas, fechas o metadata upstream.

## Configuración recomendada

### Cuenta

1. Entrar en Pinterest y comprobar si ya existe una cuenta de David.
2. Si existe y es legítima, convertirla/revisarla como Business en lugar de duplicarla.
3. Si no existe, crear una única cuenta Business gratuita.
4. Nombre visible: `David Porto Díaz`.
5. Avatar/foto oficial coherente con la web.
6. Bio breve factual: escritor + obras + recursos de escritura, sin keyword stuffing.
7. Website: `https://davidportodiaz.com/`.

No fijar handle aquí: debe capturarse de la cuenta real y comprobar disponibilidad.

### Claim del dominio

Preferencia técnica para este repo: **HTML tag** o **HTML file**, porque permiten verificar sin tocar DNS global y Pinterest confirma que pueden retirarse después del claim.

Si la UI entrega un HTML tag:

1. copiar el valor exacto generado por Pinterest;
2. localizar el owner real del `<head>` en el sistema de build/shell;
3. no editar outputs generados a mano si existe builder;
4. añadir el tag únicamente en el owner correcto;
5. regenerar;
6. pasar QA estático específico;
7. desplegar;
8. verificar `https://davidportodiaz.com/` desde Pinterest;
9. confirmar `Claimed` en Settings;
10. retirar el tag solo después de verificar que Pinterest mantiene el claim, tal como documenta su ayuda;
11. regenerar/CI/producción de nuevo si se retira.

El DNS TXT queda como alternativa si el HTML tag/file falla. No tocar MX/SPF/DKIM/DMARC ni sustituir otros TXT.

## Piloto orgánico mínimo

No crear docenas de tableros ni contenido diario.

### Tableros iniciales — máximo 4

1. `Las manecillas del recuerdo`
2. `Samuel entre mundos · Noveris`
3. `Fantasía, worldbuilding y sistemas de magia`
4. `Herramientas y recursos para escritores`

No crear `Prensa`, `Eventos`, `Frases`, etc. salvo que haya volumen real que justifique un tablero independiente.

### 6–10 Pins iniciales

Reutilizar activos propios ya existentes y páginas con valor real, por ejemplo:

- portada/página oficial de Manecillas;
- fragmento o recurso visual de Manecillas sin reproducir texto excesivo;
- Samuel/Noveris;
- artículo fuerte `libros-fantasia-juvenil-espanola-2025-2026`;
- portal fantasy;
- sistemas de magia;
- una o dos herramientas para escritores con uso real.

Cada Pin debe enviar a la URL canónica específica, no siempre a Home.

No crear contenido visual genérico solo para alimentar Pinterest. Si un Pin necesita una creatividad nueva, debe reutilizar el sistema visual ya aprobado de la web/libros.

## Metadata / Rich Pins

No tocar código preventivamente.

Primero reclamar el dominio y publicar el piloto. Después comprobar qué metadata extrae Pinterest de Open Graph/Schema existente. Solo abrir una PR técnica si falta un campo que produzca un fallo real reproducible y el cambio mejora también otros consumidores.

No duplicar title/description/schema solo para Pinterest.

## Medición

Baseline al publicar el piloto:

- impresiones;
- guardados;
- outbound clicks;
- top Pins;
- top URLs;
- followers si los hubiera;
- referrals `pinterest.com` / `pin.it` observados en la analítica propia.

Revisiones 30/60/90 días.

### Decisión

- si genera referrals, saves o descubrimiento sostenido con mantenimiento bajo → mantener y reutilizar contenido evergreen;
- si la señal es prácticamente cero → `NO_GO_LOW_SIGNAL` y no dedicar calendario editorial específico.

No instalar Pinterest Tag/Ads tracking para este piloto: Business Analytics + analítica propia son suficientes.

## Web / sameAs

Solo si queda una cuenta pública, estable e inequívocamente oficial:

- valorar `Person.sameAs`;
- valorar enlace social visible únicamente si la cuenta tendrá actividad real.

No añadir un perfil vacío únicamente para engordar `sameAs`.

Si se añade a la web:

1. usar el owner factual/social central;
2. regenerar shell/derivados;
3. actualizar tests/allowlists si aplican;
4. CI;
5. QA móvil/escritorio;
6. producción.

## Guardrails

- `ZERO_AD_SPEND`.
- No Pinterest Ads.
- No contenido masivo/automatizado de baja calidad.
- No inventar handle/profile URL.
- No usar Pinterest como fuente de metadata bibliográfica.
- No añadir otro tracker third-party sin necesidad demostrada.
- No crear cuenta duplicada si existe una anterior.
- No convertir el canal en una obligación diaria antes de medir señal.

## Pasos exactos para Claude

1. Auditar cuenta existente por email/nombre y búsqueda interna.
2. Guardar URL/handle solo si es la cuenta real.
3. Convertir/crear Business gratuita según corresponda.
4. Completar identidad + web.
5. Iniciar claim de `davidportodiaz.com`.
6. Usar HTML tag/file preferentemente y aplicar cualquier cambio de código en una PR separada con owner/build/QA correctos.
7. Verificar claim.
8. Crear como máximo 4 tableros iniciales.
9. Publicar 6–10 Pins evergreen de activos ya existentes.
10. Verificar destinos canónicos y previews.
11. Capturar baseline de Analytics.
12. Guardar profile URL.
13. Valorar `Person.sameAs` solo si el perfil es estable/activo.
14. Revisar a 30/60/90 días y decidir mantener/parar.

## Criterio de cierre

`EXISTING_ACCOUNT_AUDITED · FREE_BUSINESS_ACCOUNT_READY · PROFILE_IDENTITY_CURRENT · WEBSITE_CLAIMED · DOMAIN_VERIFICATION_QA_DONE · PILOT_BOARDS_CREATED · SIX_TO_TEN_EVERGREEN_PINS_PUBLISHED · CANONICAL_DESTINATIONS_VERIFIED · BASELINE_CAPTURED · SITE_SAMEAS_DECIDED · ZERO_AD_SPEND`

O, tras piloto:

`NO_GO_LOW_SIGNAL · METRICS_RECORDED · NO_EXTRA_CONTENT_BURDEN · ZERO_SPEND`

## Fuentes oficiales

- Business account: https://help.pinterest.com/en/business/article/get-a-business-account
- Claim website: https://help.pinterest.com/en/business/article/claim-your-website
