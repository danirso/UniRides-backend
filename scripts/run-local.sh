#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
python_bin="${PYTHON_BIN:-venv/bin/python}"
if ! "$python_bin" -c 'import sys; assert sys.prefix != sys.base_prefix; import uvicorn, alembic, fastapi, sqlalchemy, psycopg2, fastapi_mail' >/dev/null 2>&1; then
  echo "Check the virtual environment and install requirements-dev.txt before starting the API." >&2
  exit 1
fi

export ENVIRONMENT=dev
export ALLOW_LOCAL_TEST_EMAILS=true
export API_BASE_URL=http://127.0.0.1:8000
export DATABASE_URL=postgresql://local_user:local_password@127.0.0.1:5434/unirides_local
export TEST_DATABASE_URL=postgresql://test_user:test_password@127.0.0.1:5433/test_db
export SECRET_KEY=local_development_only_do_not_use_in_production
export GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-not-configured}"
export MAIL_USERNAME=local
export MAIL_PASSWORD=local
export MAIL_FROM=noreply@example.com
export MAIL_FROM_NAME=UniRides
export MAIL_SERVER=127.0.0.1
export MAIL_PORT=1025
export MAIL_STARTTLS=false
export MAIL_SSL_TLS=false
export MAIL_USE_CREDENTIALS=false
export MAIL_VALIDATE_CERTS=true

docker compose -f compose.local.yml up --wait
"$python_bin" -m alembic upgrade head
printf 'API: http://127.0.0.1:8000/docs\nLocal inbox: http://127.0.0.1:8025\n'
exec "$python_bin" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
