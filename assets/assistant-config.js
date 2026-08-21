// Configuración pública del asistente. No contiene secretos.
// El modo remoto requiere dos llaves: remoteEnabled=true aquí y ASSISTANT_ENABLED=true en el Worker.
export const ASSISTANT_PUBLIC_CONFIG = Object.freeze({
  protocolVersion: 1,
  remoteEnabled: false,
  assistantUrl: "/api/assistant",
  configUrl: "/api/assistant/config",
  turnstileSiteKey: "",
  queryMinLength: 2,
  queryMaxLength: 500,
});
