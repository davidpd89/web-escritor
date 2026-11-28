# Registra la tarea de Windows que abre el siguiente almacén de portadas antes de que el activo se llene.
# Una App de GitHub no puede crear repositorios en una cuenta personal y GITHUB_TOKEN tampoco: lo hace el gh del
# dueño, una vez al día (scripts/almacen_portadas.py auto; no toca nada por debajo de 700 MB).
# Copia los scripts a una carpeta estable para que borrar ramas o worktrees no la rompa.
$ErrorActionPreference = 'Stop'
$taskName = 'WEB_Libros_Almacen_Portadas'
$dest = Join-Path $env:LOCALAPPDATA 'web-escritor\almacen-portadas\scripts'
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($f in 'almacen_portadas.py', 'reading_cover_store.py') {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $f) -Destination $dest -Force
}
$python = (Get-Command python -ErrorAction Stop).Source
$gh = Split-Path (Get-Command gh -ErrorAction Stop).Source
$git = Split-Path (Get-Command git -ErrorAction Stop).Source
$ssh = Split-Path (Get-Command ssh-keygen -ErrorAction Stop).Source
$script = Join-Path $dest 'almacen_portadas.py'
$log = Join-Path (Split-Path $dest) 'almacen.log'
$cmd = "/c set `"PATH=$gh;$git;$ssh;%PATH%`" && `"$python`" `"$script`" auto >> `"$log`" 2>&1"
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $cmd
$trigger = New-ScheduledTaskTrigger -Daily -At '10:40'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force `
    -Description 'Abre el siguiente almacén de portadas si el activo pasa de 700 MB. Ver scripts/almacen_portadas.py' | Out-Null
Write-Output "Tarea $taskName registrada (10:40, recupera si el equipo estaba apagado). Log: $log"
