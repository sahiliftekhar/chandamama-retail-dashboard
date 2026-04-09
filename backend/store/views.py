# ============================================================
#  store/views.py — Health Check + System Status + Dashboard API
# ============================================================

import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from django.http import JsonResponse
from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime


def dashboard_api(request):
    """
    /api/dashboard/ — AJAX endpoint for dashboard KPI filtering.
    Supports range: today, week, month, year, all, custom
    Returns current + previous period for trend badges.
    """
    range_type = request.GET.get("range", "today")
    from_date  = request.GET.get("from_date")
    to_date    = request.GET.get("to_date")
    section_id = request.GET.get("section", "all")

    from django.db.models import Q
    from .models import Sale, Section
    from datetime import timedelta

    today = timezone.now().date()

    def make_date_filter(rtype, fd=None, td=None):
        if rtype == "today":
            return Q(sold_date=today), Q(sold_date=today - timedelta(days=1))
        elif rtype == "week":
            cur_start = today - timedelta(days=7)
            prev_start = today - timedelta(days=14)
            return Q(sold_date__gte=cur_start), Q(sold_date__gte=prev_start, sold_date__lt=cur_start)
        elif rtype == "month":
            from datetime import date
            cur_start = today.replace(day=1)
            # Previous month
            prev_end = cur_start - timedelta(days=1)
            prev_start = prev_end.replace(day=1)
            return Q(sold_date__gte=cur_start), Q(sold_date__gte=prev_start, sold_date__lte=prev_end)
        elif rtype == "year":
            cur_start = today.replace(month=1, day=1)
            prev_start = cur_start.replace(year=cur_start.year - 1)
            prev_end = cur_start - timedelta(days=1)
            return Q(sold_date__gte=cur_start), Q(sold_date__gte=prev_start, sold_date__lte=prev_end)
        elif rtype == "custom" and fd and td:
            cur_f = datetime.strptime(fd, "%Y-%m-%d").date()
            cur_t = datetime.strptime(td, "%Y-%m-%d").date()
            span = (cur_t - cur_f).days + 1
            prev_t = cur_f - timedelta(days=1)
            prev_f = prev_t - timedelta(days=span - 1)
            return Q(sold_date__range=(cur_f, cur_t)), Q(sold_date__range=(prev_f, prev_t))
        else:
            return Q(), None  # all time — no comparison

    cur_filter, prev_filter = make_date_filter(range_type, from_date, to_date)

    # ── Section Filter ───────────────────────────────────────
    section_filter = Q()
    if section_id != "all":
        try:
            sec = Section.objects.get(pk=section_id)
            section_filter = Q(product__category__section=sec)
        except Section.DoesNotExist:
            pass

    qs = Sale.objects.filter(cur_filter & section_filter)

    # ── KPI Calculations ─────────────────────────────────────
    total_revenue = float(qs.aggregate(t=Sum("selling_price"))["t"] or 0)
    total_profit  = float(qs.aggregate(t=Sum("profit"))["t"] or 0)
    total_units   = int(qs.aggregate(t=Sum("quantity"))["t"] or 0)
    margin_pct    = round(total_profit / total_revenue * 100, 1) if total_revenue else 0

    # ── Previous Period ───────────────────────────────────────
    rev_pct = profit_pct = units_pct = None
    if prev_filter is not None:
        qs_prev = Sale.objects.filter(prev_filter & section_filter)
        prev_revenue = float(qs_prev.aggregate(t=Sum("selling_price"))["t"] or 0)
        prev_profit  = float(qs_prev.aggregate(t=Sum("profit"))["t"] or 0)
        prev_units   = int(qs_prev.aggregate(t=Sum("quantity"))["t"] or 0)

        def pct_change(cur, prev):
            if prev == 0:
                return 100.0 if cur > 0 else 0.0
            return round((cur - prev) / prev * 100, 1)

        rev_pct    = pct_change(total_revenue, prev_revenue)
        profit_pct = pct_change(total_profit,  prev_profit)
        units_pct  = pct_change(total_units,   prev_units)

    return JsonResponse({
        "revenue":     total_revenue,
        "profit":      total_profit,
        "units":       total_units,
        "margin_pct":  margin_pct,
        "rev_pct":     rev_pct,
        "profit_pct":  profit_pct,
        "units_pct":   units_pct,
    })





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