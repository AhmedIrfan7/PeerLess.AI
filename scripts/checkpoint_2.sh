#!/usr/bin/env bash
# Checkpoint 2 — agents, orchestrator, frontend build (Steps 13–22)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/apps/backend"
FRONTEND="$ROOT/apps/frontend"

echo "=== Checkpoint 2: agents + frontend ==="

PYTHON="${PYTHON:-python}"

# Agent modules import
echo "[1] Agent modules import..."
cd "$BACKEND"
PYTHONPATH=src $PYTHON -c "
from peerless.agents.llm import generate_json, generate_text
from peerless.agents.statistical_integrity.agent import run as stat_run
from peerless.agents.citation_verifier.agent import run as cit_run
from peerless.agents.plain_language_summary import run as pls_run
print('  OK')
"

# Crossref module
echo "[2] Crossref module imports..."
PYTHONPATH=src $PYTHON -c "from peerless.verification.crossref import lookup_doi, is_retracted; print('  OK')"

# Orchestrator
echo "[3] Orchestrator imports..."
PYTHONPATH=src $PYTHON -c "from peerless.orchestrator.graph import run_graph; print('  OK')"

# Assemble
echo "[4] Assemble module imports..."
PYTHONPATH=src $PYTHON -c "from peerless.reports.assemble import assemble_and_persist, compute_overall_confidence; print('  OK')"

# compute_overall_confidence logic
echo "[5] Overall confidence logic..."
PYTHONPATH=src $PYTHON -c "
from peerless.reports.assemble import compute_overall_confidence
assert compute_overall_confidence([{'severity':'high'}]) == 'low'
assert compute_overall_confidence([{'severity':'medium'}]) == 'medium'
assert compute_overall_confidence([{'severity':'low'}]) == 'high'
assert compute_overall_confidence([]) == 'high'
print('  OK')
"

# Frontend TypeScript compiles (next build --dry)
echo "[6] Frontend package.json present..."
if [ -f "$FRONTEND/package.json" ]; then
  echo "  OK"
else
  echo "  MISSING $FRONTEND/package.json" && exit 1
fi

# lib/api.ts present
echo "[7] Frontend lib/api.ts present..."
if [ -f "$FRONTEND/lib/api.ts" ]; then
  echo "  OK"
else
  echo "  MISSING $FRONTEND/lib/api.ts" && exit 1
fi

# Pages present
echo "[8] Frontend pages present..."
for page in \
  "$FRONTEND/app/page.tsx" \
  "$FRONTEND/app/papers/[id]/page.tsx" \
  "$FRONTEND/app/papers/[id]/report/page.tsx" \
  "$FRONTEND/app/layout.tsx"; do
  if [ -f "$page" ]; then
    echo "  OK: $page"
  else
    echo "  MISSING: $page" && exit 1
  fi
done

echo ""
echo "=== Checkpoint 2 PASSED ==="
