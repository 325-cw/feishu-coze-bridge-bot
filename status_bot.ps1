$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root 'runtime\bot.pid'

if (-not (Test-Path $pidFile)) {
    Write-Output 'Bot is not running.'
    exit 0
}

$pidText = (Get-Content $pidFile -Raw).Trim()
if (-not $pidText) {
    Write-Output 'Bot PID file is empty.'
    exit 0
}

$process = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
if ($process) {
    Write-Output "Bot is running with PID $($process.Id)"
} else {
    Write-Output "Bot PID file exists, but process $pidText is not running."
}
