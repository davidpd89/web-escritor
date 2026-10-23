# Install / remove / query the Windows scheduled task that refreshes the social snapshot.
#   .\install-social-refresh-task.ps1 install [-Publish]
#   .\install-social-refresh-task.ps1 remove | status | run
param([ValidateSet('install','remove','status','run')][string]$Action = 'status', [switch]$Publish)
$name = 'web-escritor-social-refresh'
$script = Join-Path $PSScriptRoot 'gpt_social_refresh.py'
switch ($Action) {
  'install' {
    $py = (Get-Command python).Source
    $args = "`"$script`"" + $(if ($Publish) { ' --publish' } else { '' })
    $act = New-ScheduledTaskAction -Execute $py -Argument $args -WorkingDirectory (Split-Path $PSScriptRoot -Parent | Split-Path -Parent)
    $t1 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 6)
    $t2 = New-ScheduledTaskTrigger -AtLogOn
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $name -Action $act -Trigger $t1,$t2 -Settings $set -Force | Out-Null
    "installed $name (every 6 h, at logon, run missed after restart)"
  }
  'remove' { Unregister-ScheduledTask -TaskName $name -Confirm:$false; "removed $name" }
  'run' { Start-ScheduledTask -TaskName $name; "started $name" }
  'status' { Get-ScheduledTask -TaskName $name | Get-ScheduledTaskInfo | Select-Object LastRunTime, LastTaskResult, NextRunTime }
}
