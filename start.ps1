[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$apiUrl = "http://127.0.0.1:8000/api/health"
$webUrl = "http://127.0.0.1:5173"

function Test-Url([string]$Url) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-ForUrl([string]$Url, [string]$Name) {
    foreach ($attempt in 1..30) {
        if (Test-Url $Url) { return }
        Start-Sleep -Milliseconds 500
    }
    throw "$Name did not start within 15 seconds. Check the port and run its command manually for logs."
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.13+ first."
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js 22+ first."
}

if ($Install) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
    & python -m pip install -e $root
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    Push-Location (Join-Path $root "apps\web")
    try { & npm.cmd install } finally { Pop-Location }
} elseif (-not (Test-Path (Join-Path $root "apps\web\node_modules"))) {
    throw "Frontend dependencies are missing. First run: powershell -ExecutionPolicy Bypass -File .\start.ps1 -Install"
}

if (-not (Test-Url $apiUrl)) {
    Write-Host "Starting API: $apiUrl" -ForegroundColor Cyan
    Start-Process -FilePath python -ArgumentList "apps/api/run.py" -WorkingDirectory $root -WindowStyle Hidden
    Wait-ForUrl $apiUrl "API"
} else {
    Write-Host "API is already running." -ForegroundColor DarkYellow
}

if (-not (Test-Url $webUrl)) {
    Write-Host "Starting web: $webUrl" -ForegroundColor Cyan
    Start-Process -FilePath npm.cmd -ArgumentList "run", "dev" -WorkingDirectory (Join-Path $root "apps\web") -WindowStyle Hidden
    Wait-ForUrl $webUrl "Web"
} else {
    Write-Host "Web is already running." -ForegroundColor DarkYellow
}

Write-Host "`nAnshi Sim is ready: $webUrl" -ForegroundColor Green
if (-not $NoBrowser) { Start-Process $webUrl }
