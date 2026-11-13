# Registra la tarea de Windows que vigila Telegram/Discord a las 11:25 y 11:50 (hora local).
# Copia el script a una carpeta estable para que borrar ramas o worktrees no la rompa.
$ErrorActionPreference = 'Stop'
$taskName = 'WEB_Libros_Telegram_Vigilante'
$dest = Join-Path $env:LOCALAPPDATA 'web-escritor\telegram-guardian'
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'telegram_guardian.py') -Destination $dest -Force
$python = (Get-Command python -ErrorAction Stop).Source
$gh = Split-Path (Get-Command gh -ErrorAction Stop).Source
$script = Join-Path $dest 'telegram_guardian.py'
$log = Join-Path $dest 'vigilante.log'
$cmd = "/c set `"PATH=$gh;%PATH%`" && `"$python`" `"$script`" >> `"$log`" 2>&1"
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $cmd
$triggers = @((New-ScheduledTaskTrigger -Daily -At '11:25'), (New-ScheduledTaskTrigger -Daily -At '11:50'))
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Force `
    -Description 'Lanza el ciclo de Telegram/Discord si GitHub no lo ha arrancado. Ver scripts/telegram_guardian.py' | Out-Null
Write-Output "Tarea $taskName registrada (11:25 y 11:50). Log: $log"
