<#
  Despliega el bot buscador de la comunidad (/libro en Discord y @DavidPortoLibrosBot en Telegram).
  Lo ejecuta David desde la raíz del repositorio: powershell -ExecutionPolicy Bypass -File bots/deploy-community-bot.ps1
  Pide los secretos por teclado (ocultos); no se guardan en el repositorio ni en el historial.
  Pasos: worker en Cloudflare -> secretos -> Interactions Endpoint de Discord -> invitar la app -> registrar /libro -> webhook y comandos de Telegram.
  Opciones: -SoloTelegram o -SoloDiscord repiten solo esa parte (el worker ya desplegado).
#>
param(
  [switch]$SoloTelegram,
  [switch]$SoloDiscord,
  [string]$GuildId = '1566732369656946738'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$config = 'wrangler.community-bot.jsonc'
$ejemplo = 'wrangler.community-bot.example.jsonc'

function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Pedir($texto) { Read-Host $texto }
function PedirSecreto($texto) {
  $s = Read-Host $texto -AsSecureString
  $p = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($p).Trim() } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p) }
}
function Esperar($texto) { [void](Read-Host "$texto  [Intro para seguir]") }

foreach ($cmd in 'node', 'npx') {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Falta $cmd en el PATH (instala Node.js 20 o superior)." }
}
if (-not (Test-Path $config)) { Copy-Item $ejemplo $config; Write-Host "Creado $config a partir del ejemplo." }

$hacerDiscord = -not $SoloTelegram
$hacerTelegram = -not $SoloDiscord

# 1. Worker
Paso '1/5 Desplegar el worker en Cloudflare (si pide iniciar sesión, se abre el navegador)'
$salida = (npx wrangler deploy -c $config 2>&1 | Out-String)
Write-Host $salida
if ($LASTEXITCODE -ne 0) { throw 'wrangler deploy ha fallado.' }
$m = [regex]::Match($salida, 'https://[\w.-]+\.workers\.dev')
$base = if ($m.Success) { $m.Value } else { Pedir 'URL del worker (https://….workers.dev)' }
$base = $base.TrimEnd('/')
Write-Host "Worker: $base"

# 2. Secretos (wrangler secret bulk lee un JSON: valores exactos, sin saltos de línea añadidos)
Paso '2/5 Secretos del worker'
$secretos = @{}
if ($hacerDiscord) {
  $secretos.DISCORD_PUBLIC_KEY = PedirSecreto 'Discord Public Key (Developer Portal -> General Information)'
}
$telegramToken = $null
$webhookSecret = $null
if ($hacerTelegram) {
  $telegramToken = PedirSecreto 'Token de @DavidPortoLibrosBot (BotFather)'
  $bytes = New-Object byte[] 32
  [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $webhookSecret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
  $secretos.TELEGRAM_BOT_TOKEN = $telegramToken
  $secretos.TELEGRAM_WEBHOOK_SECRET = $webhookSecret
}
$tmp = Join-Path $env:TEMP ("cb-secrets-" + [guid]::NewGuid().ToString('N') + '.json')
try {
  [IO.File]::WriteAllText($tmp, ($secretos | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
  npx wrangler secret bulk $tmp -c $config
  if ($LASTEXITCODE -ne 0) { throw 'wrangler secret bulk ha fallado.' }
} finally {
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

if ($hacerDiscord) {
  # 3. Endpoint de interacciones (Discord valida la firma con un PING, por eso va después de los secretos)
  Paso '3/5 Discord: Interactions Endpoint URL'
  Write-Host "En https://discord.com/developers/applications -> tu aplicación -> General Information,"
  Write-Host "pega en «Interactions Endpoint URL»:  $base/discord  y pulsa Save (debe guardar sin error)."
  Esperar 'Cuando esté guardado'

  # 4. Invitar la app y registrar /libro
  Paso '4/5 Discord: invitar la aplicación y registrar /libro'
  $appId = Pedir 'Application ID (General Information)'
  $invite = "https://discord.com/oauth2/authorize?client_id=$appId&scope=applications.commands&guild_id=$GuildId&disable_guild_select=true"
  Write-Host "Abre y autoriza en el servidor «Club de lectura · David Porto»:`n  $invite"
  Start-Process $invite
  Esperar 'Cuando esté autorizada'
  $env:DISCORD_APP_ID = $appId
  $env:DISCORD_GUILD_ID = $GuildId
  $env:DISCORD_BOT_TOKEN = PedirSecreto 'Bot Token (pestaña Bot -> Reset Token)'
  try {
    node bots/register-discord-commands.mjs
    if ($LASTEXITCODE -ne 0) { throw 'El registro del comando ha fallado.' }
  } finally {
    Remove-Item Env:DISCORD_BOT_TOKEN -ErrorAction SilentlyContinue
  }
  Write-Host 'Debe haber impreso «200 /libro».'
}

if ($hacerTelegram) {
  # 5. Webhook y comandos de Telegram
  Paso '5/5 Telegram: webhook y comandos'
  $api = "https://api.telegram.org/bot$telegramToken"
  $body = @{ url = "$base/telegram"; secret_token = $webhookSecret; allowed_updates = @('message', 'inline_query'); drop_pending_updates = $true } | ConvertTo-Json
  $r = Invoke-RestMethod -Method Post -Uri "$api/setWebhook" -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
  Write-Host "setWebhook: $($r.ok) $($r.description)"
  $cmds = @{ commands = @(@{ command = 'buscar'; description = 'Busca libros del catálogo' }) } | ConvertTo-Json -Depth 4
  $r = Invoke-RestMethod -Method Post -Uri "$api/setMyCommands" -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($cmds))
  Write-Host "setMyCommands: $($r.ok)"
  $info = Invoke-RestMethod -Uri "$api/getWebhookInfo"
  Write-Host "Webhook activo: $($info.result.url)  pendientes: $($info.result.pending_update_count)"
  Write-Host "Falta a mano en @BotFather: /setinline -> @DavidPortoLibrosBot -> «qué te apetece leer…» (activa el modo inline)."
}

Paso 'Pruebas'
if ($hacerDiscord) { Write-Host '  Discord:  /libro busco: fantasía para 11 años' }
if ($hacerTelegram) { Write-Host '  Telegram: /buscar thriller (al bot) y @DavidPortoLibrosBot terror (en cualquier chat)' }
Write-Host "  Salud del worker: $base"
