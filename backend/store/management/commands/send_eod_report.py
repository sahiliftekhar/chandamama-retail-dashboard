from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.utils import timezone
from store.models import Sale, Stock
from store.utils import send_whatsapp_alert


class Command(BaseCommand):
    help = 'Sends daily EOD sales report via WhatsApp'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # ── Today's Sales Summary ─────────────────────────────────
        sales = Sale.objects.filter(sold_date__date=today)

        total_revenue = sales.aggregate(t=Sum("selling_price"))["t"] or 0
        total_profit  = sales.aggregate(t=Sum("profit"))["t"] or 0
        total_units   = sales.aggregate(t=Sum("quantity"))["t"] or 0
        total_orders  = sales.count()

        margin_pct = round(
            float(total_profit) / float(total_revenue) * 100, 1
        ) if total_revenue else 0

        # ── Top 5 products today ──────────────────────────────────
        top_products = (
            sales
            .values("product__name")
            .annotate(units=Sum("quantity"), revenue=Sum("selling_price"))
            .order_by("-units")[:5]
        )

        top_lines = ""
        for i, p in enumerate(top_products, 1):
            top_lines += f"\n  {i}. {p['product__name']} — {p['units']} pcs (₹{p['revenue']:.0f})"

        if not top_lines:
            top_lines = "\n  No sales today"

        # ── Category breakdown ────────────────────────────────────
        cat_data = (
            sales
            .values("product__category__name", "product__category__section__name")
            .annotate(rev=Sum("selling_price"))
            .order_by("-rev")
        )
        cat_lines = ""
        for c in cat_data:
            cat_lines += f"\n  • {c['product__category__section__name']} › {c['product__category__name']}: ₹{c['rev']:.0f}"

        if not cat_lines:
            cat_lines = "\n  No category data"

        # ── Low stock count ───────────────────────────────────────
        low_count = sum(
            1 for s in Stock.objects.select_related("product")
            if s.quantity <= s.product.low_stock_threshold
        )

        # ── Build message ─────────────────────────────────────────
        message = f"""
🏪 *ChandaMama Retail — EOD Report*
📅 Date: {today.strftime("%d %B %Y")}
━━━━━━━━━━━━━━━━━━━━

💰 *Revenue:* ₹{total_revenue:.0f}
📈 *Profit:* ₹{total_profit:.0f} ({margin_pct}% margin)
🛒 *Units Sold:* {total_units}
📋 *Transactions:* {total_orders}

🔥 *Top Products Today:*{top_lines}

🏷️ *Category Breakdown:*{cat_lines}

⚠️ *Low Stock SKUs:* {low_count} items need reorder

━━━━━━━━━━━━━━━━━━━━
✅ End of Day Report Complete
        """.strip()

        try:
            send_whatsapp_alert(message)
            self.stdout.write(self.style.SUCCESS(
                f'✅ EOD report sent for {today}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Failed to send EOD report: {e}'
            ))