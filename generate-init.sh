#!/bin/sh
set -e

echo "🔧 Generating init.sql from template..."
envsubst < /docker-entrypoint-initdb.d/mysql-init-template.sql > /docker-entrypoint-initdb.d/init.sql
echo "✅ init.sql generated."