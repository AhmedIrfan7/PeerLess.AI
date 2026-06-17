# PEERLESS.AI — PowerShell helper (replaces Makefile on Windows)
# Usage: .\run.ps1 <target>
#   .\run.ps1 infra       — start Postgres + Redis + ChromaDB
#   .\run.ps1 migrate     — run Alembic DB migrations
#   .\run.ps1 backend     — start FastAPI (uvicorn --reload)
#   .\run.ps1 frontend    — start Next.js dev server
#   .\run.ps1 test        — run all 38 backend tests
#   .\run.ps1 demo        — upload grim_violation demo paper
#   .\run.ps1 demo-pvalue — upload pvalue_inconsistency demo paper

param([string]$Target = "help")

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Python = "C:\Users\ahmed\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}

function Infra {
    Write-Host "Starting infrastructure (Postgres, Redis, ChromaDB)..." -ForegroundColor Cyan
    docker compose up -d postgres redis chromadb
    Write-Host "Done. Wait ~5s for Postgres to be ready, then run: .\run.ps1 migrate" -ForegroundColor Green
}

function Migrate {
    Write-Host "Running Alembic migrations..." -ForegroundColor Cyan
    $env:PYTHONPATH = "$Root\apps\backend\src"
    Push-Location "$Root\apps\backend"
    & $Python -m alembic upgrade head
    Pop-Location
    Write-Host "Migrations complete." -ForegroundColor Green
}

function Backend {
    Write-Host "Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Cyan
    $env:PYTHONPATH = "$Root\apps\backend\src"
    Push-Location "$Root\apps\backend"
    & $Python -m uvicorn peerless.main:app --reload --port 8000
    Pop-Location
}

function Frontend {
    Write-Host "Starting Next.js frontend on http://localhost:3000 ..." -ForegroundColor Cyan
    Push-Location "$Root\apps\frontend"
    npm run dev
    Pop-Location
}

function Test {
    Write-Host "Running backend tests..." -ForegroundColor Cyan
    $env:PYTHONPATH = "$Root\apps\backend\src"
    Push-Location "$Root\apps\backend"
    & $Python -m pytest tests/ -q
    Pop-Location
}

function Demo {
    param([string]$Paper = "grim_violation")
    Write-Host "Uploading demo paper: $Paper ..." -ForegroundColor Cyan
    & $Python "$Root\scripts\demo_upload.py" --paper $Paper
}

function Help {
    Write-Host ""
    Write-Host "PEERLESS.AI — run.ps1 targets:" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 infra        start Postgres + Redis + ChromaDB"
    Write-Host "  .\run.ps1 migrate      run DB migrations (after infra is up)"
    Write-Host "  .\run.ps1 backend      start FastAPI on :8000  (terminal 1)"
    Write-Host "  .\run.ps1 frontend     start Next.js on :3000  (terminal 2)"
    Write-Host "  .\run.ps1 test         run all 38 backend tests"
    Write-Host "  .\run.ps1 demo         upload grim_violation demo paper"
    Write-Host "  .\run.ps1 demo-pvalue  upload pvalue_inconsistency demo paper"
    Write-Host ""
}

switch ($Target) {
    "infra"        { Infra }
    "migrate"      { Migrate }
    "backend"      { Backend }
    "frontend"     { Frontend }
    "test"         { Test }
    "demo"         { Demo "grim_violation" }
    "demo-pvalue"  { Demo "pvalue_inconsistency" }
    default        { Help }
}
