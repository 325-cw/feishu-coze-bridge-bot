$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root 'runtime\bot.pid'

if (-not (Test-Path $pidFile)) {
    Write-Output 'Bot is not running (no PID file found).'
    exit 0
}

$pidText = (Get-Content $pidFile -Raw).Trim()
if (-not $pidText) {
    Remove-Item $pidFile -Force
    Write-Output 'Removed empty PID file.'
    exit 0
}

$process = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item $pidFile -Force
    Write-Output "Bot process $pidText was not running."
    exit 0
}

Stop-Process -Id $process.Id
Remove-Item $pidFile -Force
Write-Output "Stopped bot process $($process.Id)"

