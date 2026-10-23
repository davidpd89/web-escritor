# Install / remove / query the Windows scheduled task that refreshes (and publishes) the social snapshot.
#   .\install-social-refresh-task.ps1 install [-RunnerDir C:\GIT\web-escritor-social-runner] [-NoPublish]
#   .\install-social-refresh-task.ps1 remove | status | run
# RunnerDir must be a dedicated clone of main: the wrapper resets it to origin/main before every run.
# Runs every 6 h while the user is logged on; StartWhenAvailable catches up runs missed while the PC was off.
# (An AtLogOn trigger needs elevation, so it is not used.) Public updates are throttled by gpt_social_publish.py.
param([ValidateSet('install','remove','status','run')][string]$Action = 'status',
      [string]$RunnerDir = 'C:\GIT\web-escritor-social-runner', [switch]$NoPublish)
$name = 'web-escritor-social-refresh'
$state = Join-Path $env:LOCALAPPDATA 'web-escritor-social'
$wrapper = Join-Path $state 'run-refresh.ps1'
switch ($Action) {
  'install' {
    if (-not (Test-Path (Join-Path $RunnerDir '.git'))) { throw "RunnerDir is not a git clone: $RunnerDir" }
    New-Item -ItemType Directory -Force $state | Out-Null
    $flag = if ($NoPublish) { '' } else { ' --publish' }
    @"
`$ErrorActionPreference = 'Stop'
git -C '$RunnerDir' fetch --quiet origin main
git -C '$RunnerDir' reset --quiet --hard origin/main
Set-Location '$RunnerDir'
python scripts/research/gpt_social_refresh.py$flag
exit `$LASTEXITCODE
"@ | Set-Content -Path $wrapper -Encoding utf8
    $act = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$wrapper`""
    $trg = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $pr = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $name -Action $act -Trigger $trg -Settings $set -Principal $pr -Force | Out-Null
    "installed $name (every 6 h while logged on, catches up missed runs)"
  }
  'remove' { Unregister-ScheduledTask -TaskName $name -Confirm:$false; "removed $name" }
  'run' { Start-ScheduledTask -TaskName $name; "started $name" }
  'status' { Get-ScheduledTask -TaskName $name | Get-ScheduledTaskInfo | Select-Object LastRunTime, LastTaskResult, NextRunTime }
}
