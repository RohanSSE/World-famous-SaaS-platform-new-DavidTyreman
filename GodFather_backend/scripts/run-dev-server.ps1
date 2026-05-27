# Django dev server — port 8001 (8000 is often taken by Cursor IDE on Windows)
# From GodFather_backend: .\scripts\run-dev-server.ps1
# Optional: .\scripts\run-dev-server.ps1 -Port 8002

param(
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path $PSScriptRoot -Parent
Set-Location $backendRoot

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "venv not found. Create it: python -m venv venv" -ForegroundColor Red
    exit 1
}

. .\venv\Scripts\Activate.ps1

# Skip Celery/ES index rebuild on startup (infra optional for basic API)
$env:DJANGO_SKIP_KNOWLEDGE_AUTO = "1"

$inUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($inUse) {
    Write-Host "Port $Port is already in use (PID $($inUse.OwningProcess))." -ForegroundColor Yellow
    Write-Host "Try: .\scripts\run-dev-server.ps1 -Port 8002" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Django API: http://127.0.0.1:${Port}/api ===" -ForegroundColor Cyan
Write-Host "Frontend .env: VITE_API_BASE_URL=http://127.0.0.1:${Port}/api" -ForegroundColor Gray
Write-Host "Infra (optional): .\scripts\start-infra.ps1" -ForegroundColor Gray
Write-Host ""

# manage.py defaults to 127.0.0.1:8001 when no port is passed
python manage.py runserver "127.0.0.1:${Port}"
