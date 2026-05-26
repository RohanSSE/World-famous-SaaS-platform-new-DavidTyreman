# Start Godfather infra: Postgres (PGVector), Redis, Elasticsearch
# Run from GodFather_backend: .\scripts\start-infra.ps1

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path $PSScriptRoot -Parent
Set-Location $backendRoot

function Get-DockerExe {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return "docker" }
    $p = "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $p) { return $p }
    return $null
}

$docker = Get-DockerExe
if (-not $docker) {
    Write-Host "Docker not found. Install Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

Write-Host "=== Starting Postgres + Redis + Elasticsearch ===" -ForegroundColor Cyan
& $docker compose up -d postgres redis elasticsearch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Waiting for services (up to 90s)..." -ForegroundColor Cyan
$ok = @{ pg = $false; redis = $false; es = $false }

for ($i = 1; $i -le 45; $i++) {
    if (-not $ok.pg) {
        $pg = & $docker exec godfather_postgres pg_isready -U postgres -d godfather 2>$null
        if ($LASTEXITCODE -eq 0) { $ok.pg = $true; Write-Host "  Postgres OK (localhost:5433)" -ForegroundColor Green }
    }
    if (-not $ok.redis) {
        $rd = & $docker exec godfather-redis redis-cli ping 2>$null
        if ($rd -match "PONG") { $ok.redis = $true; Write-Host "  Redis OK (localhost:6379)" -ForegroundColor Green }
    }
    if (-not $ok.es) {
        try {
            $r = Invoke-RestMethod -Uri "http://localhost:9200" -TimeoutSec 3
            $ok.es = $true
            Write-Host "  Elasticsearch OK ($($r.cluster_name))" -ForegroundColor Green
        } catch { }
    }
    if ($ok.pg -and $ok.redis -and $ok.es) { break }
    Start-Sleep -Seconds 2
}

Write-Host ""
if (-not $ok.es) { Write-Host "Elasticsearch not ready — wait 1-2 min, then: curl http://localhost:9200" -ForegroundColor Yellow }
if (-not $ok.redis) { Write-Host "Redis not ready — check: docker logs godfather-redis" -ForegroundColor Yellow }
if (-not $ok.pg) { Write-Host "Postgres not ready — check: docker logs godfather_postgres" -ForegroundColor Yellow }

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host '  $env:DJANGO_SKIP_KNOWLEDGE_AUTO="0"'
Write-Host "  python manage.py migrate"
Write-Host "  python manage.py build_ai_knowledge --force"
Write-Host "  python scripts/verify_pgvector.py"
Write-Host "  celery -A project worker -l info"
Write-Host "  python manage.py runserver"
