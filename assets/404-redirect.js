// Enlaces mal formados (p. ej. "/davidportodiaz.com/cuaderno/") llegaban al 404 y
// partian las estadisticas de GoatCounter. Si la ruta lleva el dominio delante,
// reenviamos a la ruta real conservando query y hash.
(function () {
  var m = location.pathname.match(/^\/(?:www\.)?(?:davidportodiaz\.com|david-porto-preview\.[a-z0-9.-]*workers\.dev)(\/.*)?$/i);
  if (m) location.replace((m[1] || "/") + location.search + location.hash);
})();
