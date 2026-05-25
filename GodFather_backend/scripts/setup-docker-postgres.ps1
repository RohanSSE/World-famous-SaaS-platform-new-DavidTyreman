# Option A: Docker Postgres on localhost:5432 (stop Windows Postgres first)
# Run PowerShell as Administrator for best results.

$ErrorActionPreference = "Continue"
Write-Host "=== Godfather: Docker-only Postgres (port 5432) ===" -ForegroundColor Cyan

# Stop common Windows PostgreSQL service names
$serviceNames = @(
    "postgresql",
    "postgresql-x64-16",
    "postgresql-x64-15",
    "postgresql-x64-14",
    "PostgreSQL"
)

foreach ($name in $serviceNames) {
    $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -eq "Running") {
        Write-Host "Stopping Windows service: $name" -ForegroundColor Yellow
        try {
            Stop-Service -Name $name -Force
            Write-Host "Stopped $name" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop $name (run this script as Administrator): $_" -ForegroundColor Red
        }
    }
}

$backendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $backendRoot

Write-Host "`nRecreating Docker Postgres (fresh volume)..." -ForegroundColor Cyan
docker compose down -v
docker compose up -d postgres

Write-Host "Waiting for Postgres healthcheck..." -ForegroundColor Cyan
Start-Sleep -Seconds 8
docker logs godfather_postgres --tail 5

Write-Host "`nTest: docker exec godfather_postgres psql -U postgres -d godfather -c 'SELECT 1'" -ForegroundColor Cyan
docker exec godfather_postgres psql -U postgres -d godfather -c "SELECT 1"

Write-Host "`nNext (from GodFather_backend):" -ForegroundColor Green
Write-Host '  $env:DJANGO_SKIP_KNOWLEDGE_AUTO="1"'
Write-Host "  python manage.py migrate"
Write-Host "  python manage.py runserver"
Write-Host ""
Write-Host "If Django still fails auth on 5432, Windows Postgres is still bound. Use Option B: POSTGRES_PORT=5433 in .env." -ForegroundColor Yellow
