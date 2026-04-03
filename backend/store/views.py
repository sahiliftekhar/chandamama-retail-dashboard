# ============================================================
#  store/views.py — Health Check + System Status Endpoint
# ============================================================

import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check(request):
    """
    /health/ — Lightweight health check endpoint.
    Returns 200 if everything is OK, 500 if something is broken.
    """
    status   = "ok"
    checks   = {}
    http_status = 200

    # ── Database check ────────────────────────────────────────
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ms = round((time.time() - start) * 1000, 2)
        checks["database"] = {"status": "ok", "response_ms": db_ms}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        status = "error"
        http_status = 500

    # ── Quick model check ─────────────────────────────────────
    try:
        from store.models import Sale, Product, Stock
        checks["models"] = {
            "status":   "ok",
            "products": Product.objects.count(),
            "sales":    Sale.objects.count(),
            "stocks":   Stock.objects.count(),
        }
    except Exception as e:
        checks["models"] = {"status": "error", "error": str(e)}
        status = "error"
        http_status = 500

    # ── System resources ──────────────────────────────────────
    try:
        if PSUTIL_AVAILABLE:
            checks["system"] = {
                "status":           "ok",
                "cpu_percent":      psutil.cpu_percent(interval=0.1),
                "memory_percent":   psutil.virtual_memory().percent,
                "disk_percent":     psutil.disk_usage('/').percent,
            }
        else:
            checks["system"] = {"status": "unavailable"}
    except Exception:
        checks["system"] = {"status": "unavailable"}

    response = {
        "status":    status,
        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        "service":   "ChandaMama Retail Dashboard",
        "version":   "2.4",
        "checks":    checks,
    }

    return JsonResponse(response, status=http_status)


def system_status(request):
    """
    /admin/system-status/ — Detailed system status for admin.
    Requires staff login.
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    from store.models import Sale, Product, Stock, AuditLog
    from datetime import timedelta

    today = timezone.now().date()

    try:
        recent_logs = AuditLog.objects.order_by('-timestamp')[:5].values(
            'user__username', 'action', 'model_name', 'timestamp'
        )
        audit_data = [
            {
                "user":   log["user__username"],
                "action": log["action"],
                "model":  log["model_name"],
                "time":   log["timestamp"].strftime("%d %b %H:%M"),
            }
            for log in recent_logs
        ]
    except Exception:
        audit_data = []

    return JsonResponse({
        "status":    "ok",
        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "database": {
            "products":   Product.objects.count(),
            "sales_today": Sale.objects.filter(sold_date__date=today).count(),
            "low_stock":  sum(
                1 for s in Stock.objects.select_related("product")
                if s.quantity <= s.product.low_stock_threshold
            ),
        },
        "recent_activity": audit_data,
    })