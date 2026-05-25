# Start Elasticsearch for GodFather (requires Docker Desktop)
# Run from GodFather_backend: .\scripts\start-elasticsearch.ps1

$ErrorActionPreference = "Stop"

function Get-DockerExe {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        return "docker"
    }
    $candidates = @(
        "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe",
        "${env:ProgramFiles}\Docker\Docker\docker.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$docker = Get-DockerExe
if (-not $docker) {
    Write-Host ""
    Write-Host "Docker is NOT installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "STEP A — Install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  https://www.docker.com/products/docker-desktop/"
    Write-Host "  After install: restart PC, open Docker Desktop, wait until it says Running."
    Write-Host ""
    Write-Host "STEP B — Run this script again, OR run manually:" -ForegroundColor Yellow
    Write-Host '  cd GodFather_backend'
    Write-Host '  docker compose -f docker-compose.elasticsearch.yml up -d'
    Write-Host ""
    exit 1
}

$backendRoot = Split-Path $PSScriptRoot -Parent
Set-Location $backendRoot

Write-Host "Starting Elasticsearch (godfather-elasticsearch)..." -ForegroundColor Cyan
& $docker compose -f docker-compose.elasticsearch.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start. Is Docker Desktop running?" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Waiting for http://localhost:9200 ..." -ForegroundColor Cyan
$max = 60
for ($i = 1; $i -le $max; $i++) {
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:9200" -TimeoutSec 3
        Write-Host ""
        Write-Host "Elasticsearch is UP!" -ForegroundColor Green
        Write-Host "  cluster_name: $($r.cluster_name)"
        Write-Host "  name:         $($r.name)"
        Write-Host ""
        Write-Host "Open in browser: http://localhost:9200" -ForegroundColor Green
        Write-Host "Next: python manage.py build_ai_knowledge --force --sync" -ForegroundColor Yellow
        exit 0
    } catch {
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline
    }
}

Write-Host ""
Write-Host "Elasticsearch container started but port 9200 not ready yet. Wait 1-2 min and open http://localhost:9200" -ForegroundColor Yellow
exit 0
