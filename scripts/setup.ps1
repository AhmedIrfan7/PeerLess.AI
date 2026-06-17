# PEERLESS.AI — one-shot Windows setup script
# Run from the project root: .\scripts\setup.ps1
param(
    [string]$GroqKey = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "=== PEERLESS.AI setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Python ────────────────────────────────────────────────────────────────────
$Python = "C:\Users\ahmed\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python) { Write-Error "Python not found."; exit 1 }
Write-Host "[1] Python: $(&$Python --version)" -ForegroundColor Green

# ── Install backend deps ───────────────────────────────────────────────────────
Write-Host "[2] Installing backend Python dependencies..."
& $Python -m pip install -e "$Root\apps\backend[dev]" --quiet
Write-Host "    Done." -ForegroundColor Green

# ── .env file ─────────────────────────────────────────────────────────────────
$EnvFile = "$Root\.env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item "$Root\.env.example" $EnvFile
    Write-Host "[3] Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "[3] .env already exists — skipping" -ForegroundColor Yellow
}

if ($GroqKey) {
    $content = Get-Content $EnvFile -Raw
    $content = $content -replace 'GROQ_API_KEY=.*', "GROQ_API_KEY=$GroqKey"
    Set-Content $EnvFile $content -Encoding utf8
    Write-Host "    Grok API key written to .env" -ForegroundColor Green
}

# ── Frontend .env.local ────────────────────────────────────────────────────────
$FrontendEnv = "$Root\apps\frontend\.env.local"
if (-not (Test-Path $FrontendEnv)) {
    Copy-Item "$Root\apps\frontend\.env.local.example" $FrontendEnv
    Write-Host "[4] Created apps/frontend/.env.local" -ForegroundColor Green
} else {
    Write-Host "[4] apps/frontend/.env.local already exists — skipping" -ForegroundColor Yellow
}

# ── Frontend npm deps ──────────────────────────────────────────────────────────
Write-Host "[5] Installing frontend npm dependencies..."
Push-Location "$Root\apps\frontend"
npm install --silent
Pop-Location
Write-Host "    Done." -ForegroundColor Green

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start infrastructure:  docker compose up -d" -ForegroundColor Gray
Write-Host "     (then wait ~3s for Postgres to be ready)" -ForegroundColor Gray
Write-Host "  2. Run migrations:        make migrate" -ForegroundColor Gray
Write-Host "  3. Start backend:         make demo-backend    (Terminal 1)" -ForegroundColor Gray
Write-Host "  4. Start frontend:        make demo-frontend   (Terminal 2)" -ForegroundColor Gray
Write-Host "  5. Open browser:          http://localhost:3000" -ForegroundColor Gray
Write-Host "  6. Check status:          http://localhost:3000/health" -ForegroundColor Gray
Write-Host ""
if (-not $GroqKey) {
    Write-Host "TIP: No Grok key provided. Statistical checks (GRIM + p-value)" -ForegroundColor Yellow
    Write-Host "     still run via regex fallback. To enable Grok (xAI):" -ForegroundColor Yellow
    Write-Host "     .\scripts\setup.ps1 -GroqKey YOUR_KEY_HERE" -ForegroundColor Yellow
    Write-Host ""
}
