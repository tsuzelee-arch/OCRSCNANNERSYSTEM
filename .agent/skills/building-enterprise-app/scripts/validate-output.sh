#!/bin/bash
# validate-output.sh — Runs all pre-delivery checks
set -e

echo '=== Validating Server ==='
cd enterprise-todo-app/server
npx knex migrate:latest
node -e "require('./index.js')" &
SERVER_PID=$!
sleep 2
curl -f http://localhost:3001/api/health || { echo 'FAIL: Server health check'; kill $SERVER_PID; exit 1; }
kill $SERVER_PID

echo '=== Validating Client ==='
cd ../client
npm run build || { echo 'FAIL: Client build failed'; exit 1; }

echo '=== All validations passed ==='
