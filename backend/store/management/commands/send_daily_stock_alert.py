from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from store.models import Stock, Sale
from store.utils import send_whatsapp_alert


class Command(BaseCommand):
    help = "Send consolidated EOD WhatsApp summary"

    def handle(self, *args, **kwargs):

        today = timezone.now().date()

        # ===============================
        # 📊 SALES SUMMARY
        # ===============================
        sales_today = Sale.objects.filter(sold_date__date=today)

        total_revenue = sales_today.aggregate(
            total=Sum("selling_price")
        )["total"] or 0

        total_profit = sales_today.aggregate(
            total=Sum("profit")
        )["total"] or 0

        total_units = sales_today.aggregate(
            total=Sum("quantity")
        )["total"] or 0

        # ===============================
        # 🚨 LOW STOCK CHECK
        # ===============================
        low_stock_items = []

        for stock in Stock.objects.select_related("product"):
            if stock.quantity <= stock.product.low_stock_threshold:
                low_stock_items.append(
                    f"{stock.product.name} ({stock.size}) - Qty: {stock.quantity}"
                )

        # ===============================
        # 🧾 BUILD MESSAGE
        # ===============================
        message = f"""
📊 *EOD BUSINESS SUMMARY*
Date: {today.strftime("%d %b %Y")}

💰 Revenue: ₹{total_revenue}
📈 Profit: ₹{total_profit}
🛒 Units Sold: {total_units}
"""

        if low_stock_items:
            message += "\n⚠ *Low Stock Alert:*\n"
            message += "\n".join(low_stock_items)
        else:
            message += "\n✅ No low stock items today."

        send_whatsapp_alert(message)
