#!/usr/bin/env bash
# Checkpoint 1 — backend core (Steps 1–12)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/apps/backend"

echo "=== Checkpoint 1: backend core ==="

# Python available
PYTHON="${PYTHON:-python}"
echo "Using Python: $($PYTHON --version 2>&1)"

# Config loads
echo "[1] Config loads..."
cd "$BACKEND"
PYTHONPATH=src $PYTHON -c "from peerless.config import get_settings; s = get_settings(); print('  database_url prefix:', s.database_url[:20])"

# Main app instantiates
echo "[2] FastAPI app instantiates..."
PYTHONPATH=src $PYTHON -c "from peerless.main import app; print('  routes:', len(app.routes))"

# Schemas import
echo "[3] Schemas import..."
PYTHONPATH=src $PYTHON -c "from peerless.api.schemas import PaperResponse, ReportResponse, FindingResponse; print('  OK')"

# GRIM check
echo "[4] GRIM check..."
PYTHONPATH=src $PYTHON -c "
from peerless.verification.grim import grim_check
r = grim_check('2.50', 7)
print('  2.50 n=7 possible:', r.possible)
assert r.possible is False, 'Expected impossible'
r2 = grim_check('2.57', 7)
print('  2.57 n=7 possible:', r2.possible)
assert r2.possible is True, 'Expected possible'
"

# Statcheck
echo "[5] Statcheck..."
PYTHONPATH=src $PYTHON -c "
from peerless.verification.statcheck import check_t_test
r = check_t_test(2.0, 30, '0.055')
print('  t=2.0 df=30 consistent:', r.consistent)
"

# Extract import
echo "[6] Extraction module imports..."
PYTHONPATH=src $PYTHON -c "from peerless.parsing.extract import extract_paper; print('  OK')"

# Models import
echo "[7] ORM models import..."
PYTHONPATH=src $PYTHON -c "from peerless.storage.models import Paper, Report, Finding; print('  OK')"

echo ""
echo "=== Checkpoint 1 PASSED ==="
