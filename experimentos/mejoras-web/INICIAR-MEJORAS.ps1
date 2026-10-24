#requires -Version 5.1
param([int]$SitePort = 8765, [int]$DebugPort = 9331)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$branch = (& git -C $repo branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or !$branch) { throw 'No se pudo determinar la rama Git.' }
if (!(($branch -like 'lab/mejoras-*') -or ($branch -like 'research/mejoras-*') -or ($branch -like 'feature/mejoras-*'))) {
    throw "No se inicia desde '$branch'. Usa un worktree independiente lab/mejoras-* (nunca main)."
}
function Test-Port([int]$port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect('127.0.0.1', $port, $null, $null)
        if (!$async.AsyncWaitHandle.WaitOne(400)) { return $false }
        $client.EndConnect($async)
        return $true
    } catch { return $false } finally { $client.Dispose() }
}
if (Test-Port $SitePort) { throw "Puerto HTTP $SitePort en uso. No se mata ni reutiliza el proceso." }
if (Test-Port $DebugPort) { throw "Puerto CDP $DebugPort en uso. No se reutiliza sesión Edge." }
$edge = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe')
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (!$edge) {
    $edgeCommand = Get-Command msedge.exe -ErrorAction SilentlyContinue
    if ($edgeCommand) { $edge = $edgeCommand.Source }
}
if (!$edge) { throw 'Microsoft Edge no encontrado. Instala Edge o configura su ruta.' }
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (!$python) { throw 'Python 3 no encontrado en PATH.' }
& $python.Source (Join-Path $PSScriptRoot 'verificar.py')
if ($LASTEXITCODE -ne 0) { throw 'Catalogo de investigaciones invalido.' }
$profile = Join-Path $env:LOCALAPPDATA 'web-escritor-lab/edge-9331'
New-Item -ItemType Directory -Force -Path $profile | Out-Null
$server = Start-Process -FilePath $python.Source -ArgumentList @('-m','http.server',"$SitePort",'--bind','127.0.0.1') -WorkingDirectory $repo -PassThru -NoNewWindow
try {
    Start-Sleep -Seconds 1
    if ($server.HasExited) { throw 'Servidor local no pudo arrancar.' }
    $url = "http://127.0.0.1:$SitePort/"
    $args = @("--remote-debugging-port=$DebugPort", '--remote-debugging-address=127.0.0.1', "--user-data-dir=`"$profile`"", '--no-first-run', $url)
    Start-Process -FilePath $edge -ArgumentList $args | Out-Null
    Write-Host "Laboratorio: $url | Edge CDP 127.0.0.1:$DebugPort | rama $branch"
    Write-Host 'Ctrl+C en esta consola termina el servidor local. No se ejecuta GPT/Claude automaticamente.'
    while (!$server.HasExited) { Start-Sleep -Seconds 1 }
    throw 'El servidor local se ha detenido.'
} finally {
    if (!$server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
