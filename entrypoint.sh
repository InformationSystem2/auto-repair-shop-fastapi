#!/bin/sh

set -e

echo "Waiting for database to be ready..."
max_attempts=30
attempt=0
db_host="${DB_HOST:-db}"
db_port="${DB_PORT:-5432}"

while [ $attempt -lt $max_attempts ]; do
    # Try to connect to PostgreSQL
    if python3 -c "import psycopg2; psycopg2.connect(host='$db_host', port='$db_port', user='${POSTGRES_USER:-first_exam}', password='${POSTGRES_PASSWORD:-first_exam}', database='${POSTGRES_DB:-auto_repair_shop}')" > /dev/null 2>&1; then
        echo "✓ Database is ready"
        break
    fi
    echo "  Waiting for database... ($((attempt + 1))/$max_attempts)"
    sleep 1
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ Database did not become ready in time"
    exit 1
fi

echo "Running database migrations..."
alembic upgrade head || {
    echo "⚠️  Alembic upgrade failed, but continuing..."
}

echo "Running seed (creates admin user if not exists)..."
python -m app.seed || {
    echo "⚠️  Seed failed or already applied, continuing..."
}

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
