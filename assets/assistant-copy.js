// Autoridad unica de microcopy del asistente (L.2, 2026-08-23).
//
// Antes de este modulo, el HTML fuente de /asistente/ declaraba una
// experiencia ("Pregunta a esta web." / "¿Qué quieres encontrar?" / "Tu
// pregunta" / "Buscar respuesta") y assets/assistant.js la sustituia por
// otra distinta en tiempo de ejecucion ("¿Qué buscas?" / "Escribe tu
// pregunta…") sin ningun contrato compartido -- dos fuentes de verdad que
// podian divergir sin que nada lo detectara.
//
// Este objeto es la UNICA fuente de verdad para esas cadenas. El HTML
// estatico de asistente/index.html usa estos mismos valores literalmente
// (para que el estado pre-JS/no-JS ya sea el correcto, sin parpadeo de
// contenido), y assets/assistant.js los usa para todo lo que reescribe en
// tiempo de ejecucion. scripts/check-assistant-copy.py verifica que ambas
// fuentes siguen coincidiendo.
export const ASSISTANT_COPY = Object.freeze({
  heroTitle: "¿Qué buscas?",
  heroLead: "Pregúntame por los libros, fragmentos, Noveris, herramientas, editoriales, eventos o información sobre David.",
  queryLabel: "Escribe tu pregunta",
  placeholder: "Escribe tu pregunta…",
  submitAriaLabel: "Enviar pregunta",
  submitTitle: "Enviar",
  stopAriaLabel: "Detener respuesta",
  chatPanelLabel: "Chat con el asistente",
  chatLogLabel: "Conversación",
  welcomeMessage: "Hola. Dime qué buscas y te ayudo a encontrarlo en la web.",
});
