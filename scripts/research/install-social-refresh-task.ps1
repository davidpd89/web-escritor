# Install / remove / query the Windows scheduled task that refreshes (and publishes) the social snapshot.
#   .\install-social-refresh-task.ps1 install [-RunnerDir C:\GIT\web-escritor-social-runner] [-NoPublish]
#   .\install-social-refresh-task.ps1 remove | status | run
# RunnerDir must be a dedicated clone of main: the wrapper resets it to origin/main before every run.
# Runs every 6 h while the user is logged on; StartWhenAvailable catches up runs missed while the PC was off.
# Priority 4 (normal I/O): the default 7 starves git on a large clone. (An AtLogOn trigger needs elevation, so it is not used.) Public updates are throttled by gpt_social_publish.py.
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
`$env:GIT_TERMINAL_PROMPT = '0'; `$env:GCM_INTERACTIVE = 'never'
`$log = '$state\refresh.log'
function Log(`$m) { Add-Content -Path `$log -Value ("{0:u} wrapper: {1}" -f (Get-Date).ToUniversalTime(), `$m) -Encoding utf8 }
# Bounded fetch: a stuck git-remote-https once held the task until its 30 min limit, every run, for days.
`$git = Start-Process git -ArgumentList '-C','"$RunnerDir"','fetch','--quiet','--no-tags','--depth','1','origin','main' -NoNewWindow -PassThru
`$null = `$git.Handle
if (-not `$git.WaitForExit(180000)) {
  & taskkill.exe /T /F /PID `$git.Id | Out-Null
  Log 'fetch timed out after 180 s; refreshing with the current checkout'
} elseif (`$git.ExitCode -ne 0) {
  Log "fetch failed rc=`$(`$git.ExitCode); refreshing with the current checkout"
} else {
  git -C '$RunnerDir' reset --quiet --hard origin/main
}
Set-Location '$RunnerDir'
python scripts/research/gpt_social_refresh.py$flag
`$rc = `$LASTEXITCODE
Log "refresh rc=`$rc"
exit `$rc
"@ | Set-Content -Path $wrapper -Encoding utf8
    $act = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$wrapper`""
    $trg = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -Priority 4 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $pr = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $name -Action $act -Trigger $trg -Settings $set -Principal $pr -Force | Out-Null
    "installed $name (every 6 h while logged on, catches up missed runs)"
  }
  'remove' { Unregister-ScheduledTask -TaskName $name -Confirm:$false; "removed $name" }
  'run' { Start-ScheduledTask -TaskName $name; "started $name" }
  'status' { Get-ScheduledTask -TaskName $name | Get-ScheduledTaskInfo | Select-Object LastRunTime, LastTaskResult, NextRunTime }
}
