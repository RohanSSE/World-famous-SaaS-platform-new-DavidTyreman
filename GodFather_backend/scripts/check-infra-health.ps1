# Quick health check: ES, Redis, Postgres, PGVector
$ErrorActionPreference = "Continue"
$backendRoot = Split-Path $PSScriptRoot -Parent
Set-Location $backendRoot

Write-Host "=== Godfather infra health ===" -ForegroundColor Cyan

# Elasticsearch
try {
    $es = Invoke-RestMethod -Uri "http://localhost:9200" -TimeoutSec 5
    Write-Host "[OK] Elasticsearch: $($es.cluster_name) on port 9200" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Elasticsearch :9200 — $($_.Exception.Message)" -ForegroundColor Red
}

# Redis (via docker if redis-cli not installed)
$redisOk = $false
if (Get-Command redis-cli -ErrorAction SilentlyContinue) {
    $pong = redis-cli ping 2>$null
    if ($pong -eq "PONG") { $redisOk = $true }
}
if (-not $redisOk) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        $pong = docker exec godfather-redis redis-cli ping 2>$null
        if ($pong -match "PONG") { $redisOk = $true }
    }
}
if ($redisOk) {
    Write-Host '[OK] Redis PONG on port 6379' -ForegroundColor Green
} else {
    Write-Host "[FAIL] Redis :6379" -ForegroundColor Red
}

# Postgres + PGVector via Django
$env:DJANGO_SKIP_KNOWLEDGE_AUTO = "1"
python scripts/verify_pgvector.py 2>&1 | ForEach-Object { Write-Host $_ }

Write-Host "=== Done ===" -ForegroundColor Cyan
