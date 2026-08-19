<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" doctype-system="about:legacy-compat" />

  <xsl:template match="/">
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="robots" content="noindex,follow" />
        <title><xsl:value-of select="rss/channel/title" /></title>
        <style>
          :root{color-scheme:dark;--bg:#0f0d0b;--panel:#181512;--text:#f2ede6;--muted:#b9afa2;--line:#332b24;--accent:#c4944d;--max:880px}
          *{box-sizing:border-box}
          html{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}
          body{margin:0;line-height:1.65;background:radial-gradient(circle at 15% 0%,rgba(196,148,77,.10),transparent 35rem),var(--bg)}
          a{color:inherit;text-decoration-thickness:.08em;text-underline-offset:.18em}
          a:hover{color:var(--accent)}
          a:focus-visible{outline:3px solid var(--accent);outline-offset:4px;border-radius:4px}
          main{width:min(calc(100% - 32px),var(--max));margin:0 auto;padding:56px 0 72px}
          .eyebrow{margin:0 0 12px;color:var(--accent);font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
          h1{max-width:16ch;margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(2.2rem,7vw,4.8rem);line-height:.98;font-weight:500}
          .intro{max-width:66ch;margin:24px 0 0;color:var(--muted);font-size:1.02rem}
          .actions{display:flex;flex-wrap:wrap;gap:12px;margin:28px 0 44px}
          .button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 16px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:var(--panel)}
          .button.primary{border-color:var(--accent);background:var(--accent);color:#17120c;font-weight:700}
          .feed-note{padding:18px 20px;border:1px solid var(--line);border-radius:16px;background:rgba(24,21,18,.76);color:var(--muted)}
          .feed-note strong{color:var(--text)}
          .entries{display:grid;gap:16px;margin-top:28px}
          article{padding:22px;border:1px solid var(--line);border-radius:18px;background:rgba(24,21,18,.72)}
          article h2{margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(1.25rem,3vw,1.65rem);line-height:1.18;font-weight:500}
          article h2 a{text-decoration:none}
          article time{display:block;margin:10px 0 0;color:var(--accent);font-size:.78rem;letter-spacing:.02em}
          article p{margin:12px 0 0;color:var(--muted)}
          footer{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
          @media(max-width:520px){main{width:min(calc(100% - 24px),var(--max));padding-top:36px}.actions{display:grid}.button{width:100%}article{padding:18px}}
          @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
        </style>
      </head>
      <body>
        <main>
          <header>
            <p class="eyebrow">RSS · Cuaderno del autor</p>
            <h1><xsl:value-of select="rss/channel/title" /></h1>
            <p class="intro"><xsl:value-of select="rss/channel/description" /></p>
            <div class="actions">
              <a class="button primary" href="/cuaderno/">Abrir Cuaderno</a>
              <a class="button" href="/">Ir a davidportodiaz.com</a>
            </div>
          </header>

          <aside class="feed-note" aria-label="Qué es este archivo">
            <strong>Este es un feed RSS.</strong>
            Puedes copiar la dirección de esta página en tu lector de RSS para recibir nuevos artículos sin depender de redes sociales ni algoritmos.
          </aside>

          <section class="entries" aria-label="Últimos artículos">
            <xsl:for-each select="rss/channel/item">
              <article>
                <h2>
                  <a>
                    <xsl:attribute name="href"><xsl:value-of select="link" /></xsl:attribute>
                    <xsl:value-of select="title" />
                  </a>
                </h2>
                <xsl:if test="pubDate">
                  <time><xsl:value-of select="pubDate" /></time>
                </xsl:if>
                <xsl:if test="description">
                  <p><xsl:value-of select="description" /></p>
                </xsl:if>
              </article>
            </xsl:for-each>
          </section>

          <footer>
            <p>Feed oficial del Cuaderno de David Porto Díaz. La presentación visual es opcional; el contenido sigue siendo RSS 2.0 estándar.</p>
          </footer>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
