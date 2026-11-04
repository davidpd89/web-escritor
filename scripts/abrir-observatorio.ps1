#requires -Version 5.1
<#
  Abre los paneles del observatorio en Edge con el perfil habitual del usuario.
  No usa puertos, CDP, cookies, credenciales ni sesiones automatizadas.
  Ejemplos: .\scripts\abrir-observatorio.ps1
            .\scripts\abrir-observatorio.ps1 -Grupo seo
            .\scripts\abrir-observatorio.ps1 -Grupo todo
#>
[CmdletBinding()]
param(
  [ValidateSet('inicio','seo','comportamiento','social','ventas','operaciones','todo')]
  [string]$Grupo = 'inicio'
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$archivo = Join-Path $raiz 'docs\observatorio\fuentes.json'
$catalogo = Get-Content -LiteralPath $archivo -Raw -Encoding UTF8 | ConvertFrom-Json
$servicios = @($catalogo.servicios | Where-Object {
  if ($Grupo -eq 'todo') { return $true }
  if ($Grupo -eq 'inicio') { return $_.inicio -eq $true }
  return $_.grupos -contains $Grupo
})
$urls = @($servicios | ForEach-Object { $_.url } | Sort-Object -Unique)
if ($urls.Count -eq 0) { throw "No hay servicios para el grupo '$Grupo'." }
foreach ($url in $urls) {
  if ($url -notmatch '^https://[^\s"''<>]+$') { throw "URL no permitida en el catálogo: $url" }
}
$posibles = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
)
$edge = $posibles | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $edge) {
  $cmd = Get-Command msedge.exe -ErrorAction SilentlyContinue
  if ($cmd) { $edge = $cmd.Source }
}
if (-not $edge) { throw 'No se ha encontrado Microsoft Edge. Instálalo o verifica su ruta.' }
Write-Host ("Observatorio: abriendo {0} panel(es) [{1}] en Edge." -f $urls.Count, $Grupo)
Start-Process -FilePath $edge -ArgumentList (@('--new-window') + $urls)
Write-Host 'Claude Code: usa /observatorio-web con la extensión de navegador conectada mediante /chrome.'
