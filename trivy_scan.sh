#!/bin/bash
# ============================================================
#  trivy_scan.sh — Docker Image Vulnerability Scanner
#  ChandaMama Retail Dashboard
#  Run: bash trivy_scan.sh
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     🛡️  ChandaMama — Trivy Security Scanner          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Images to scan ────────────────────────────────────────────────
IMAGES=(
    "my_eod-backend:latest"
    "my_eod-frontend:latest"
    "postgres:15"
    "nginx:alpine"
)

REPORT_DIR="./security_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$REPORT_DIR"

# ── Check if Trivy is installed ───────────────────────────────────
if ! command -v trivy &> /dev/null; then
    echo "📦 Trivy not found — pulling via Docker..."
    USE_DOCKER=true
else
    USE_DOCKER=false
    echo "✅ Trivy found: $(trivy --version | head -1)"
fi

echo ""

# ── Scan each image ───────────────────────────────────────────────
TOTAL_CRITICAL=0
TOTAL_HIGH=0

for IMAGE in "${IMAGES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Scanning: $IMAGE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Clean image name for filename
    CLEAN_NAME=$(echo "$IMAGE" | tr '/:' '__')
    REPORT_FILE="$REPORT_DIR/trivy_${CLEAN_NAME}_${TIMESTAMP}.txt"
    JSON_FILE="$REPORT_DIR/trivy_${CLEAN_NAME}_${TIMESTAMP}.json"

    if [ "$USE_DOCKER" = true ]; then
        # Run Trivy via Docker
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "$PWD/$REPORT_DIR:/reports" \
            aquasec/trivy:latest image \
            --severity CRITICAL,HIGH,MEDIUM \
            --format table \
            "$IMAGE" 2>/dev/null | tee "$REPORT_FILE"

        # JSON report for CI/CD
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image \
            --severity CRITICAL,HIGH \
            --format json \
            --output "/tmp/trivy_out.json" \
            "$IMAGE" 2>/dev/null
    else
        # Run Trivy directly
        trivy image \
            --severity CRITICAL,HIGH,MEDIUM \
            --format table \
            "$IMAGE" 2>/dev/null | tee "$REPORT_FILE"

        trivy image \
            --severity CRITICAL,HIGH \
            --format json \
            --output "$JSON_FILE" \
            "$IMAGE" 2>/dev/null
    fi

    echo ""
    echo "📄 Report saved: $REPORT_FILE"
    echo ""
done

# ── Scan Python dependencies ──────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Scanning Python dependencies (requirements.txt)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQ_REPORT="$REPORT_DIR/trivy_python_deps_${TIMESTAMP}.txt"

if [ "$USE_DOCKER" = true ]; then
    docker run --rm \
        -v "$PWD/backend:/project" \
        aquasec/trivy:latest fs \
        --severity CRITICAL,HIGH,MEDIUM \
        --format table \
        /project/requirements.txt 2>/dev/null | tee "$REQ_REPORT"
else
    trivy fs \
        --severity CRITICAL,HIGH,MEDIUM \
        --format table \
        ./backend/requirements.txt 2>/dev/null | tee "$REQ_REPORT"
fi

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                  📊 Scan Complete                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📁 All reports saved in: $REPORT_DIR/"
echo "📅 Timestamp: $TIMESTAMP"
echo ""
echo "Reports:"
ls -la "$REPORT_DIR/" | grep "$TIMESTAMP"
echo ""
echo "✅ Trivy scan complete!"
echo ""
echo "🔗 Next step: View SonarQube at http://localhost:9000"
echo "   Default login: admin / admin"
echo ""