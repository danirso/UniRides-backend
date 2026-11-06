#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python_bin="${PYTHON_BIN:-venv/bin/python}"
if ! "$python_bin" -c 'import sys; raise SystemExit(sys.prefix == sys.base_prefix)' >/dev/null 2>&1; then
  echo "Ambiente virtual não encontrado em $python_bin. Crie o venv e instale requirements-dev.txt." >&2
  exit 1
fi
if ! "$python_bin" -m pytest --version >/dev/null 2>&1; then
  echo "Pytest não está instalado em $python_bin. Instale requirements-dev.txt nesse ambiente." >&2
  exit 1
fi

docker compose -f compose.test.yml up --wait

export ENVIRONMENT=dev
export API_BASE_URL=http://127.0.0.1:8000
export DATABASE_URL=postgresql://test_user:test_password@127.0.0.1:5433/test_db
export TEST_DATABASE_URL="$DATABASE_URL"
export SECRET_KEY=local_test_key_only
export GOOGLE_MAPS_API_KEY=local_test_key_only
export MAIL_USERNAME=local-test@example.com
export MAIL_PASSWORD=local_test_password_only
export MAIL_FROM=local-test@example.com
export MAIL_SERVER=localhost
export MAIL_PORT=587

"$python_bin" -m pytest "$@"
