import assert from "node:assert/strict";
import fs from "node:fs";
import worker, { dispatch, REPO, WORKFLOW } from "../workers/intake-dispatch.mjs";

// El dispatch pide la carga sobre main y con respaldo=true: el reloj del workflow decide si carga.
const llamadas = [];
const ok = async (url, opts) => { llamadas.push({ url, opts }); return new Response(null, { status: 204 }); };
assert.equal(await dispatch({ GH_DISPATCH_TOKEN: "t" }, ok), 204);
assert.equal(llamadas[0].url, `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`);
assert.equal(llamadas[0].opts.method, "POST");
assert.equal(llamadas[0].opts.headers.Authorization, "Bearer t");
assert.deepEqual(JSON.parse(llamadas[0].opts.body), { ref: "main", inputs: { respaldo: true } });

// Un fallo de GitHub o un token caducado se lanza: el Cron Trigger queda como fallido y se ve en Cloudflare.
await assert.rejects(dispatch({ GH_DISPATCH_TOKEN: "t" }, async () => new Response("Bad credentials", { status: 401 })), /dispatch 401/);
await assert.rejects(dispatch({}, ok), /GH_DISPATCH_TOKEN/);

// scheduled() espera al dispatch con waitUntil.
const esperas = [];
globalThis.fetch = ok;
await worker.scheduled({}, { GH_DISPATCH_TOKEN: "t" }, { waitUntil: p => esperas.push(p) });
assert.equal(await esperas[0], 204);

// El workflow acepta el input y el reloj lo trata como un cron (pasa por ci_intake_backup.py): sin carga doble.
const wf = fs.readFileSync(new URL("../.github/workflows/reading-catalogue-sync.yml", import.meta.url), "utf8");
assert.match(wf, /\n {6}respaldo:\n/, "workflow_dispatch declara el input respaldo");
assert.match(wf, /github\.event_name == 'schedule' \|\| inputs\.respaldo/, "el reloj descarga ci_intake_backup.py también para el respaldo");
assert.match(wf, /workflow_dispatch:true:\*\) python3 scripts\/ci_intake_backup\.py/, "el dispatch de respaldo decide como un cron");

// Los crons del Worker caen después del cron de GitHub de las 00:17 y antes del último respaldo (03:17).
const conf = fs.readFileSync(new URL("../wrangler.intake-dispatch.jsonc", import.meta.url), "utf8");
assert.match(conf, /"crons": \["20 0 \* \* \*", "50 1 \* \* \*"\]/);
console.log("OK intake-dispatch worker");
