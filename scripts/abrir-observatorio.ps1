#requires -Version 5.1
<#
  Un solo navegador Edge para el observatorio: perfil persistente + CDP local :9221.
  Uso: .\scripts\abrir-observatorio.ps1 [-Grupo todo|seo|...]
  Cierra esta ventana de Edge al terminar: mientras el puerto está abierto
  cualquier proceso local podría controlar las cuentas iniciadas en este perfil.
#>
[CmdletBinding()]
param(
  [ValidateSet('todo','seo','comportamiento','social','ventas','operaciones','inicio')]
  [string]$Grupo = 'todo'
)
$ErrorActionPreference = 'Stop'
$puerto = 9221
$perfil = Join-Path $env:LOCALAPPDATA 'web-escritor\edge-observatorio'
$catalogo = Get-Content -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'docs\observatorio\fuentes.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$servicios = @($catalogo.servicios | Where-Object {
  if ($Grupo -eq 'todo') { return $true }
  if ($Grupo -eq 'inicio') { return $_.inicio -eq $true }
  return $_.grupos -contains $Grupo
})
$urls = @($servicios | ForEach-Object { $_.url } | Sort-Object -Unique)
if ($urls.Count -eq 0) { throw "No hay servicios para el grupo $Grupo." }
foreach ($url in $urls) {
  if ($url -notmatch '^https://[^\s"''<>]+$') { throw "URL no permitida en el inventario: $url" }
}
$posibles = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
)
$edge = $posibles | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $edge) {
  $cmd = Get-Command 'msedge.exe' -ErrorAction SilentlyContinue
  if ($cmd) { $edge = $cmd.Source }
}
if (-not $edge) { throw 'No encuentro Microsoft Edge en este Windows.' }
$endpoint = "http://127.0.0.1:$puerto/json/version"
$version = $null
try { $version = Invoke-RestMethod -Uri $endpoint -TimeoutSec 2 } catch {}
if ($version -and $version.Browser -notmatch 'Edg') {
  throw "El puerto $puerto ya pertenece a otro navegador. Cierra ese navegador antes de continuar."
}
if (-not $version) {
  $socket = New-Object System.Net.Sockets.TcpClient
  $ocupado = $false
  try {
    $socket.Connect('127.0.0.1', $puerto)
    $ocupado = $true
  } catch {
    # No hay servicio escuchando en el puerto: Edge lo utilizará.
  } finally {
    $socket.Dispose()
  }
  if ($ocupado) { throw "El puerto $puerto está ocupado por otro programa. Libéralo antes de continuar." }
}
if (-not (Test-Path -LiteralPath $perfil)) { New-Item -ItemType Directory -Path $perfil -Force | Out-Null }
$argsEdge = @(
  '--new-window',
  '--remote-debugging-address=127.0.0.1',
  "--remote-debugging-port=$puerto",
  "--user-data-dir=`"$perfil`""
) + $urls
Start-Process -FilePath $edge -ArgumentList $argsEdge
$activo = $false
for ($i = 0; $i -lt 24; $i++) {
  try {
    $check = Invoke-RestMethod -Uri $endpoint -TimeoutSec 1
    if ($check.Browser -match 'Edg') { $activo = $true; break }
  } catch {}
  Start-Sleep -Milliseconds 250
}
if (-not $activo) {
  throw "Edge ha sido lanzado, pero no responde en el puerto $puerto. Comprueba edge://version y si la depuración está permitida."
}
Write-Host "Observatorio: $($urls.Count) webs abiertas en Edge. Puerto: 127.0.0.1:$puerto"
Write-Host "Perfil persistente: $perfil"
Write-Host "Inicia sesión en cada web la primera vez. Luego Claude Code: /observatorio-web"
