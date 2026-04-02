#!/bin/bash
# setup-project.sh — Bootstraps the enterprise-todo-app project
# Creates server/ and client/ directories, installs all dependencies,
# runs database migrations, and verifies setup.

set -e  # Exit on any error

echo '=== Step 1: Create project structure ==='
mkdir -p enterprise-todo-app/server enterprise-todo-app/client

echo '=== Step 2: Initialize and install server ==='
cd enterprise-todo-app/server
npm init -y
npm install express better-sqlite3 knex bcryptjs jsonwebtoken zod cors dotenv
npm install -D nodemon eslint prettier

echo '=== Step 3: Run migrations ==='
npx knex migrate:latest

echo '=== Step 4: Initialize and install client ==='
cd ../client
npm create vite@latest . -- --template react
npm install
npm install axios react-router-dom react-hook-form @hookform/resolvers zod

echo '=== Setup complete. Run scripts/validate-output.sh to verify. ==='
