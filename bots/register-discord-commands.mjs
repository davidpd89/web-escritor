// Registra el slash command /libro en el servidor de Discord (instantáneo; global tarda hasta 1 h).
// Uso: DISCORD_APP_ID=… DISCORD_BOT_TOKEN=… DISCORD_GUILD_ID=… node bots/register-discord-commands.mjs
// El token se pasa por entorno y no se guarda en ningún fichero.
const { DISCORD_APP_ID: app, DISCORD_BOT_TOKEN: token, DISCORD_GUILD_ID: guild } = process.env;
if (!app || !token) throw new Error('Faltan DISCORD_APP_ID y DISCORD_BOT_TOKEN en el entorno');

export const COMANDOS = [{
  name: 'libro',
  description: 'Busca libros del catálogo de David Porto y te da el enlace',
  description_localizations: { 'es-ES': 'Busca libros del catálogo de David Porto y te da el enlace' },
  options: [{ type: 3, name: 'busco', description: 'Qué te apetece leer: género, tema, edad, precio, formato o autor', required: true, max_length: 300 }],
  contexts: [0, 1, 2],
  integration_types: [0, 1],
}];

const url = guild ? `https://discord.com/api/v10/applications/${app}/guilds/${guild}/commands` : `https://discord.com/api/v10/applications/${app}/commands`;
const r = await fetch(url, { method: 'PUT', headers: { Authorization: `Bot ${token}`, 'content-type': 'application/json' }, body: JSON.stringify(COMANDOS) });
console.log(r.status, r.ok ? (await r.json()).map(c => `/${c.name}`).join(' ') : await r.text());
