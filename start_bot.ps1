$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
$envFile = Join-Path $root '.env'
$runtimeDir = Join-Path $root 'runtime'
$pidFile = Join-Path $runtimeDir 'bot.pid'
$stdoutLog = Join-Path $runtimeDir 'stdout.log'
$stderrLog = Join-Path $runtimeDir 'stderr.log'

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found: $venvPython"
}

if (-not (Test-Path $envFile)) {
    throw ".env file not found: $envFile"
}

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path $pidFile) {
    $existingPid = (Get-Content $pidFile -Raw).Trim()
    if ($existingPid) {
        $running = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
        if ($running) {
            Write-Output "Bot already running with PID $existingPid"
            exit 0
        }
    }
}

$processPathUpper = [Environment]::GetEnvironmentVariable('PATH', 'Process')
$removedUpperPath = $false
if ($processPathUpper -ne $null) {
    Remove-Item Env:PATH -ErrorAction SilentlyContinue
    $removedUpperPath = $true
}

try {
    $process = Start-Process `
        -FilePath $venvPython `
        -ArgumentList '-m', 'bot_service.service' `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru
}
finally {
    if ($removedUpperPath) {
        Set-Item Env:PATH $processPathUpper
    }
}

Set-Content -Path $pidFile -Value $process.Id -Encoding ASCII
Write-Output "Started bot with PID $($process.Id)"
