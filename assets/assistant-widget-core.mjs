export const ASSISTANT_WIDGET_HINT_KEY = "davidporto-assistant-widget-hint-v2";

export function normalizeWidgetPath(value) {
  const raw = String(value || "/").split(/[?#]/, 1)[0] || "/";
  return raw.startsWith("/") ? raw.replace(/\/{2,}/g, "/") : `/${raw}`;
}

export function shouldMountAssistantWidget(pathname) {
  const path = normalizeWidgetPath(pathname);
  return !/^\/asistente(?:\/|$)/.test(path);
}

export function assistantContextStarters(pathname) {
  const path = normalizeWidgetPath(pathname);
  if (path.startsWith("/las-manecillas-del-recuerdo")) {
    return [
      "¿De qué trata Las manecillas del recuerdo?",
      "¿Dónde puedo leer un fragmento?",
      "¿Cuándo se publica Las manecillas del recuerdo?",
    ];
  }
  if (path.startsWith("/libros/samuel-entre-mundos") || path.startsWith("/fragmento") || path.startsWith("/universo/noveris")) {
    return [
      "¿De qué trata Samuel entre mundos?",
      "¿Qué es Noveris?",
      "¿Dónde puedo leer el primer capítulo?",
    ];
  }
  if (path.startsWith("/herramientas") || path.startsWith("/editoriales") || path.startsWith("/convocatorias-escritores") || path.startsWith("/recursos/herramientas-para-escritores")) {
    return [
      "¿Qué herramientas gratuitas tienes para escritores?",
      "¿Dónde busco editoriales que acepten manuscritos?",
      "¿Qué convocatorias para escritores hay en la web?",
    ];
  }
  if (path.startsWith("/prensa") || path.startsWith("/eventos") || path.startsWith("/premios")) {
    return [
      "¿Dónde está el kit de prensa?",
      "¿Qué eventos y firmas aparecen en la web?",
      "¿Cómo puedo contactar con David?",
    ];
  }
  return [
    "¿Qué puedo encontrar en esta web?",
    "¿Qué libros ha publicado David Porto Díaz?",
    "¿Qué herramientas gratuitas hay para escritores?",
  ];
}

export function isTrustedWidgetMessage(origin, expectedOrigin, source, expectedSource) {
  return Boolean(expectedOrigin && origin === expectedOrigin && source && source === expectedSource);
}
