#requires -Version 5.1
param([int]$SitePort = 8765, [int]$DebugPort = 9331, [string]$IdeaId = '', [string]$Familia = '', [string]$Canal = '', [switch]$Simular, [switch]$SoloVista)
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
# Seleccion offline recuperable. No inicia llamadas a GPT ni Claude.
$selector = @((Join-Path $PSScriptRoot 'rotacion.py'))
if ($IdeaId) {
    $selector += @('--elegir', $IdeaId)
} else {
    $selector += '--siguiente'
    if ($Familia) { $selector += @('--familia', $Familia) }
    if ($Canal) { $selector += @('--canal', $Canal) }
}
$rawTask = & $python.Source @selector
if ($LASTEXITCODE -ne 0) { throw 'No se pudo reservar una investigacion. Usa --ver-estado o --liberar en rotacion.py.' }
$job = ($rawTask | Out-String | ConvertFrom-Json)
if (-not $job.disponible) { throw 'No quedan ideas elegibles. Revisa catalogo.json.' }
Write-Host ""
Write-Host ("Investigacion reservada: {0} | {1}" -f $job.tarea.id, $job.tarea.titulo)
Write-Host ("Canal: {0} | Familia: {1}" -f $job.tarea.canal, $job.tarea.familia)
Write-Host "GPT: experimentos/mejoras-web/contratos/GPT-INVESTIGAR.md"
Write-Host "Claude: experimentos/mejoras-web/contratos/CLAUDE-REVISAR.md"
Write-Host "No se ha enviado nada a GPT/Claude: orquestador local aun pendiente."
if ($Simular) {
    Write-Host 'SIMULACION sin navegador, consultas ni PR.'
    & $python.Source (Join-Path $PSScriptRoot 'motor/ciclo.py') --simular
    exit $LASTEXITCODE
}
if (-not $SoloVista) {
    if (-not $env:LAB_MEJORAS_PROJECT_ID) { throw 'Configura LAB_MEJORAS_PROJECT_ID con el ID de tu Project ChatGPT de mejoras antes de iniciar la automatizacion real.' }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Falta GitHub CLI (gh).' }
    if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { throw 'Falta Claude Code CLI.' }
    & $python.Source -c 'import playwright.sync_api'
    if ($LASTEXITCODE -ne 0) { throw 'Falta playwright en este Python.' }
}
$env:LAB_MEJORAS_CDP_PORT = "$DebugPort"
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
    if ($SoloVista) {
        Write-Host 'SoloVista: no se consulta GPT/Claude, pulsa Ctrl+C para cerrar.'
        while (!$server.HasExited) { Start-Sleep -Seconds 1 }
    } else {
        Write-Host 'Iniciando descubrimiento -> GPT -> Claude -> validacion -> PR draft (solo base lab).'
        Write-Host 'Ctrl+C interrumpe el ciclo; reabrir recupera el expediente y el chat persistidos.'
        & $python.Source (Join-Path $PSScriptRoot 'motor/ciclo.py') --continuo --publicar-pr
        if ($LASTEXITCODE -ne 0) { throw 'El director de mejoras se detuvo; consulta su estado, no se marca exito.' }
    }
} finally {
    if (!$server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
