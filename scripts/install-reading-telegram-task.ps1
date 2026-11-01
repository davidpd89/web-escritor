param(
    [Parameter(Mandatory=$true)][string]$PrivateRoot,
    [Parameter(Mandatory=$true)][string]$PythonExecutable
)
$ErrorActionPreference = 'Stop'
$taskName = 'WEB_Libros_Telegram_Novedades'
$sourceScripts = $PSScriptRoot
$resolvedRoot = [IO.Path]::GetFullPath($PrivateRoot)
if (!(Test-Path -LiteralPath (Join-Path $resolvedRoot 'channels.json')) -or
    !(Test-Path -LiteralPath (Join-Path $resolvedRoot 'bot-token.txt'))) {
    throw 'Configure the private channel and token before installing the worker.'
}
if (!(Test-Path -LiteralPath $PythonExecutable)) { throw 'Python executable missing.' }
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task already exists. Inspect it before updating; no existing task was changed.'
}
$runtime = Join-Path $resolvedRoot 'runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
# Freeze the imported code. Future PR edits cannot silently change a live task.
$modules = @('reading_telegram_worker','reading_telegram','reading_amazon_market',
    'reading_ratings_refresh','reading_intake_core','reading_editorial_sources',
    'reading_generic_source','reading_planeta_source','reading_taxonomy')
foreach ($module in $modules) {
    Copy-Item -LiteralPath (Join-Path $sourceScripts ($module + '.py')) -Destination $runtime
}
$worker = Join-Path $runtime 'reading_telegram_worker.py'
$arguments = '"' + $worker + '" --root "' + $resolvedRoot + '" --send'
$action = New-ScheduledTaskAction -Execute $PythonExecutable -Argument $arguments -WorkingDirectory $runtime
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 12) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description 'Novedades del día desde el catálogo editorial y enlaces de producto verificados; estado y token privados locales.' | Out-Null
Write-Output 'Installed WEB_Libros_Telegram_Novedades. Requires this computer awake, online and the user logged in.'
