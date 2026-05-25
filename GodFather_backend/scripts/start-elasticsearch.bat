@echo off
REM Start Elasticsearch via Docker Compose (GodFather_backend folder)
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-elasticsearch.ps1"
pause
