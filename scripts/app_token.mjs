#!/usr/bin/env node
// Token de instalación de la App web-escritor-reparador, sin dependencias (crypto de Node).
// Lee REPARADOR_APP_ID, REPARADOR_APP_INSTALLATION_ID y REPARADOR_APP_PRIVATE_KEY del entorno y escribe el token
// en stdout, nada más: quien lo llama lo pasa como GH_TOKEN y nunca lo imprime. Caduca en una hora, así que se
// genera justo antes de usarlo, no al empezar un paso largo.
import { createSign } from 'node:crypto';

const { REPARADOR_APP_ID: appId, REPARADOR_APP_INSTALLATION_ID: installation, REPARADOR_APP_PRIVATE_KEY: key } = process.env;
if (!appId || !installation || !key) {
  console.error('app_token: faltan REPARADOR_APP_ID, REPARADOR_APP_INSTALLATION_ID o REPARADOR_APP_PRIVATE_KEY');
  process.exit(2);
}
const b64 = (value) => Buffer.from(typeof value === 'string' ? value : JSON.stringify(value)).toString('base64url');
const now = Math.floor(Date.now() / 1000);
// iat 60 s atrás por desfase de reloj; exp a 9 min (GitHub admite 10 como máximo).
const unsigned = `${b64({ alg: 'RS256', typ: 'JWT' })}.${b64({ iat: now - 60, exp: now + 540, iss: String(appId) })}`;
const signature = createSign('RSA-SHA256').update(unsigned).sign(key.replace(/\\n/g, '\n')).toString('base64url');

const response = await fetch(`https://api.github.com/app/installations/${installation}/access_tokens`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${unsigned}.${signature}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'web-escritor-carga',
  },
  signal: AbortSignal.timeout(30000),
});
if (!response.ok) {
  console.error(`app_token: GitHub respondió ${response.status}`);
  process.exit(1);
}
const { token } = await response.json();
if (!token) {
  console.error('app_token: respuesta sin token');
  process.exit(1);
}
process.stdout.write(token);
