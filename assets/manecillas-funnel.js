// Funnel de muestra de Las manecillas del recuerdo (H.2, 2026-08-23).
//
// Contrato: eventos GoatCounter con identidad de libro explicita en el
// propio nombre (book=manecillas), para no mezclarse con el funnel de
// Samuel (que usa sus propios nombres: abrir-modal-comprar en
// assets/samuel-buy-modal.js, comprar-amazon-papel, etc.) bajo un mismo
// evento generico sin identidad.
//
//   sample-start-manecillas    -- el lector abre la pagina de la muestra
//                                 real (no la ficha del libro).
//   sample-complete-manecillas -- el lector llega al final de la muestra
//                                 (CTA final visible), umbral de consumo
//                                 significativo.
//
// Sin doble conteo: cada evento tiene un guard de "ya disparado" en esta
// misma carga de pagina, y el observer se desconecta nada mas disparar.
//
// buy_open/buy_click (H.2, punto 3): NO se instrumentan todavia -- no
// existe un CTA/tienda real verificable para Manecillas (la CTA final de
// esta pagina enlaza a la ficha del libro y a la lista de espera, no a un
// punto de venta). El evento correcto mientras tanto sigue siendo
// "newsletter-manecillas" (ya emitido por el formulario en
// las-manecillas-del-recuerdo/index.html via script.js), que ya lleva
// identidad de libro en el propio nombre. Cuando exista una tienda real,
// anadir aqui `buy-open-manecillas`/`buy-click-manecillas` siguiendo el
// mismo patron que assets/samuel-buy-modal.js -- no antes.
//
// Depende de _gcEvent, ya global (definido por script.js, cargado antes
// que este fichero).
(function () {
  const firstFragment = document.getElementById("fragmento-1");
  const finalCta = document.getElementById("cta-final");
  if (!firstFragment || !finalCta) return; // pagina distinta a la esperada: no instrumentar a ciegas

  let completeFired = false;

  // "Entrar en la muestra real" es abrir esta URL -- el primer fragmento
  // suele quedar debajo del pliegue (cabecera + hero + intro), asi que
  // gatear el inicio a un IntersectionObserver del propio fragmento-1
  // dependeria del tamano de viewport en vez del hecho real: el lector ya
  // esta en la pagina de la muestra.
  _gcEvent("sample-start-manecillas", "Muestra: inicio (Las manecillas del recuerdo)");

  const completeObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting && !completeFired) {
        completeFired = true;
        _gcEvent("sample-complete-manecillas", "Muestra: final (Las manecillas del recuerdo)");
        completeObserver.disconnect();
        break;
      }
    }
  }, { threshold: 0.3 });
  completeObserver.observe(finalCta);
})();
