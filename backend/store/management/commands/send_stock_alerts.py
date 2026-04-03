from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Max, F
from django.utils import timezone
from store.models import Sale, Stock
from store.utils import send_whatsapp_alert

DEAD_STOCK_DAYS = 90


class Command(BaseCommand):
    help = 'Sends low stock and dead stock alerts via WhatsApp'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # ── Low Stock ─────────────────────────────────────────────
        low_critical = []
        low_warning  = []

        for stock in Stock.objects.select_related(
            "product", "product__category", "product__category__section"
        ).order_by("quantity"):
            thr = stock.product.low_stock_threshold
            if stock.quantity <= thr:
                sec  = stock.product.category.section.name \
                       if stock.product.category.section else ""
                line = f"• {stock.product.name} ({stock.size}) — {stock.quantity} left"
                if stock.quantity <= max(1, thr // 3):
                    low_critical.append(line)
                else:
                    low_warning.append(line)

        # ── Dead Stock ────────────────────────────────────────────
        dead_cutoff  = today - timedelta(days=DEAD_STOCK_DAYS)
        sold_recently = Sale.objects.filter(
            sold_date__gte=dead_cutoff
        ).values_list("product_id", flat=True).distinct()

        dead_items = (
            Stock.objects
            .filter(quantity__gt=0)
            .exclude(product_id__in=sold_recently)
            .select_related("product", "product__category")
            .annotate(last_sold=Max("product__sale__sold_date"))
            .order_by(F("last_sold").asc(nulls_first=True))[:10]
        )

        dead_lines = []
        for s in dead_items:
            ls   = s.last_sold.date() if s.last_sold else None
            days = (today - ls).days if ls else None
            days_str = f"{days}d ago" if days else "Never sold"
            try:
                price = float(s.product.pricing.selling_price or 0)
            except Exception:
                price = 0
            at_risk = round(price * s.quantity, 0)
            dead_lines.append(
                f"• {s.product.name} ({s.size}) — {s.quantity} pcs | Last: {days_str} | ₹{at_risk:.0f} at risk"
            )

        # ── Skip if nothing to report ─────────────────────────────
        if not low_critical and not low_warning and not dead_lines:
            self.stdout.write(self.style.SUCCESS('✅ All stock levels healthy — no alerts needed'))
            return

        # ── Build message ─────────────────────────────────────────
        message_parts = [
            f"⚠️ *ChandaMama Stock Alert*",
            f"📅 {today.strftime('%d %B %Y')}",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        if low_critical:
            message_parts.append(f"\n🔴 *CRITICAL — Reorder Immediately ({len(low_critical)} items):*")
            message_parts.extend(low_critical)

        if low_warning:
            message_parts.append(f"\n🟡 *LOW STOCK — Reorder Soon ({len(low_warning)} items):*")
            message_parts.extend(low_warning)

        if dead_lines:
            message_parts.append(f"\n☠️ *DEAD STOCK — No Sale in {DEAD_STOCK_DAYS}+ Days ({len(dead_lines)} items):*")
            message_parts.extend(dead_lines)

        message_parts.append("\n━━━━━━━━━━━━━━━━━━━━")
        message_parts.append("📊 View full report: localhost/admin/")

        message = "\n".join(message_parts)

        try:
            send_whatsapp_alert(message)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Stock alert sent — {len(low_critical)} critical, '
                f'{len(low_warning)} low, {len(dead_lines)} dead'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Failed to send stock alert: {e}'
            ))