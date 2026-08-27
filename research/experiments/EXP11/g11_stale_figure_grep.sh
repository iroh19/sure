#!/bin/bash
# EXP11 -- Manuscript-Wide Stale-Figure Grep. Read-only against sure-project
# and the pipeline's own initial_context/ and paper_workspace/ directories.
set -euo pipefail

SURE=/Users/batuhancitak/Desktop/sure-project
PIPE=/Users/batuhancitak/Desktop/Experiments/PoggioAI-results/project_000

EXCLUDE='/venv/\|/__pycache__/\|/\.git/\|/data/sure_dataset/\|/data/frames/\|results\.csv\|/runs/\|/node_modules/\|/dist/\|/build/'

echo "=== 0.695 in sure-project (text/doc files, excluding YOLO label noise + build artifacts) ==="
grep -rn "0\.695" "$SURE" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.txt" \
  --include="*.html" --include="*.rst" 2>/dev/null \
  | grep -v "$EXCLUDE" || true

echo ""
echo "=== 0.719 in sure-project (text/doc files, excluding YOLO label noise + build artifacts) ==="
grep -rn "0\.719" "$SURE" \
  --include="*.md" --include="*.py" --include="*.json" --include="*.txt" \
  --include="*.html" --include="*.rst" 2>/dev/null \
  | grep -v "$EXCLUDE" || true

echo ""
echo "=== 0.695 in pipeline initial_context/ ==="
grep -rn "0\.695" "$PIPE/initial_context/" 2>/dev/null || echo "(none)"

echo ""
echo "=== 0.695 in pipeline paper_workspace/ (files containing it) ==="
grep -rln "0\.695" "$PIPE/paper_workspace/" 2>/dev/null || echo "(none)"

echo ""
echo "=== 0.719 in pipeline initial_context/ ==="
grep -rn "0\.719" "$PIPE/initial_context/" 2>/dev/null || echo "(none)"
