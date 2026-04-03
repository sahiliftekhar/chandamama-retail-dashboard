#!/bin/bash
# ============================================================
#  sonar_scan.sh — SonarQube Code Quality Scanner
#  ChandaMama Retail Dashboard
#  Run AFTER SonarQube is up: bash sonar_scan.sh
# ============================================================

SONAR_URL="http://localhost:9000"
SONAR_TOKEN=""   # Will be set after first login
PROJECT_KEY="chandamama-retail-dashboard"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   📊 ChandaMama — SonarQube Code Quality Scanner    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Wait for SonarQube to be ready ───────────────────────────────
echo "⏳ Waiting for SonarQube to be ready..."
until curl -sf "$SONAR_URL/api/system/status" | grep -q '"status":"UP"'; do
    echo "   SonarQube starting up... (this takes ~2 minutes first time)"
    sleep 10
done
echo "✅ SonarQube is UP!"
echo ""

# ── Check if sonar-scanner is available ──────────────────────────
if ! command -v sonar-scanner &> /dev/null; then
    echo "📦 sonar-scanner not found — running via Docker..."
    USE_DOCKER=true
else
    USE_DOCKER=false
    echo "✅ sonar-scanner found"
fi

echo ""
echo "📋 Instructions:"
echo "   1. Open: $SONAR_URL"
echo "   2. Login: admin / admin"
echo "   3. Change password when prompted"
echo "   4. Go to: My Account → Security → Generate Token"
echo "   5. Copy token and paste below"
echo ""

# ── Get token from user ───────────────────────────────────────────
read -p "🔑 Paste your SonarQube token here: " SONAR_TOKEN

if [ -z "$SONAR_TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

echo ""
echo "🔍 Running SonarQube analysis on backend code..."
echo ""

# ── Run scan ──────────────────────────────────────────────────────
if [ "$USE_DOCKER" = true ]; then
    docker run --rm \
        --network my_eod_default \
        -v "$PWD/backend:/usr/src" \
        sonarsource/sonar-scanner-cli:latest \
        -Dsonar.projectKey=$PROJECT_KEY \
        -Dsonar.projectName="ChandaMama Retail Dashboard" \
        -Dsonar.projectVersion=2.4 \
        -Dsonar.sources=/usr/src \
        -Dsonar.language=py \
        -Dsonar.python.version=3.11 \
        -Dsonar.host.url=http://sonarqube:9000 \
        -Dsonar.token=$SONAR_TOKEN \
        -Dsonar.exclusions="**/migrations/**,**/__pycache__/**,**/staticfiles/**,**/logs/**,**/backups/**"
else
    cd backend
    sonar-scanner \
        -Dsonar.projectKey=$PROJECT_KEY \
        -Dsonar.token=$SONAR_TOKEN
    cd ..
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║              ✅ Analysis Complete!                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "🌐 View results at: $SONAR_URL/dashboard?id=$PROJECT_KEY"
echo ""
echo "What SonarQube checks:"
echo "  🐛 Bugs          — Code that will likely cause errors"
echo "  🔒 Vulnerabilities — Security hotspots in your code"
echo "  💨 Code Smells   — Maintainability issues"
echo "  📋 Duplications  — Repeated code blocks"
echo "  📊 Coverage      — Test coverage percentage"
echo ""