#!/usr/bin/env bash
# Codespaces bootstrap.
#
# Installs what runs fast and is genuinely useful immediately: the rule engine,
# the knowledge-base tests, the agent tests and pgvector-backed retrieval.
#
# It deliberately does NOT download AQUA-1B or the detector weights. Those are
# gigabytes and most visitors want to read the code and run the tests, not wait
# for a model. Instructions for the full stack are printed at the end.
set -euo pipefail

echo "==> PostgreSQL + pgvector"
sudo apt-get update -qq
sudo apt-get install -y -qq postgresql postgresql-contrib >/dev/null
PGVER=$(ls /usr/lib/postgresql | head -1)
sudo apt-get install -y -qq "postgresql-${PGVER}-pgvector" >/dev/null 2>&1 || {
  echo "    pgvector package unavailable; RAG will fall back to no-retrieval mode"
}
sudo service postgresql start
sudo -u postgres psql -qc "CREATE USER vscode SUPERUSER LOGIN;" 2>/dev/null || true
sudo -u postgres createdb -O vscode sure_rag 2>/dev/null || true
psql -d sure_rag -qc "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

echo "==> Python dependencies (backend + retrieval)"
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt
pip install -q "sentence-transformers>=3.0" "psycopg[binary]>=3.2" "pgvector>=0.3"

echo "==> Frontend dependencies"
(cd frontend && npm ci --silent)

echo "==> Verifying"
(cd backend && python -m pytest test_decision.py -q)
python -m pytest llm-service/test_knowledge.py llm-service/test_agent.py -q
(cd llm-service && python eval.py --rule-only >/dev/null && echo "decision-engine eval: 8/8")

cat <<'MSG'

Ready. What works right now:

  cd backend && python -m pytest test_decision.py -v      rule engine, 18 tests
  python -m pytest llm-service/test_agent.py -v           agent tools + loop, 48 tests
  cd llm-service && python eval.py --rule-only            decision-engine eval
  cd llm-service && python -m rag.ingest                  index the knowledge base
  cd llm-service && python -m rag.bench                   chunking/embedding benchmark

The dashboard, against the recorded session:

  cd frontend && VITE_DEMO=1 npm run dev

For the full stack you also need the model and the detector weights:

  weights   gh release download --pattern 'best.pt' -D sure_models/sure_v1/weights
  llm       cd llm-service && pip install -r requirements.txt   (downloads AQUA-1B on first run)

MSG
