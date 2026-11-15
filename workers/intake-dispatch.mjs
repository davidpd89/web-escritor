// Reloj externo de la carga nocturna (P0-4, .ci/fable-direccion-2026-11-15.md, hallazgo H4).
//
// GitHub retrasa o descarta los `schedule` cuando Actions va cargado (15/11: la carga de las 00:17 UTC arrancó a
// las 08:28 y la siguiente a las 11:09). Los Cron Triggers de Cloudflare saltan a su hora: este Worker pide un
// `workflow_dispatch` de reading-catalogue-sync.yml con `respaldo=true`. Con ese input el reloj del workflow pasa
// por scripts/ci_intake_backup.py, igual que los cron, así que nunca hay carga doble: si ya hay una carga en curso
// o en verde esta noche, el dispatch termina sin cargar.
//
// Secreto: GH_DISPATCH_TOKEN, token fine-grained solo de este repositorio con «Actions: write»
// (`wrangler secret put GH_DISPATCH_TOKEN --config wrangler.intake-dispatch.jsonc`, por stdin, nunca en un fichero).

export const REPO = "davidpd89/web-escritor";
export const WORKFLOW = "reading-catalogue-sync.yml";

export async function dispatch(env, fetchImpl = fetch) {
  if (!env.GH_DISPATCH_TOKEN) throw new Error("falta el secreto GH_DISPATCH_TOKEN");
  const res = await fetchImpl(`https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "intake-dispatch-worker",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ref: "main", inputs: { respaldo: true } }),
  });
  // 204 sin cuerpo; cualquier otra respuesta se lanza para que el Cron Trigger quede como fallido en Cloudflare.
  if (res.status !== 204) throw new Error(`dispatch ${res.status}: ${(await res.text()).slice(0, 300)}`);
  return res.status;
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },
};
