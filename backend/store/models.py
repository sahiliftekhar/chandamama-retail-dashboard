from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from django.db.models import Sum

# ── Fix 3: Size range detection ───────────────────────────────────
def expand_size_range(size_str):
    """
    Expands garment size ranges into individual sizes.
    Always even numbers (garment sizing convention).

    Examples:
        "16-18" → ["16", "18"]
        "16-32" → ["16","18","20","22","24","26","28","30","32"]
        "20-30" → ["20","22","24","26","28","30"]
        "M"     → ["M"]  (non-range — returned as-is)
        "NA"    → ["NA"]
    """
    import re
    size_str = size_str.strip()
    match = re.match(r'^(\d+)-(\d+)$', size_str)
    if match:
        start = int(match.group(1))
        end   = int(match.group(2))
        if start < end and start >= 10:  # valid garment range
            return [str(i) for i in range(start, end + 1, 2)]
    return [size_str]  # not a range — return as-is


# -----------------------------
# SECTION (Male, Female, Kids)
# -----------------------------
class Section(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# -----------------------------
# CATEGORY (Upperwear, Bottomwear)
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        unique_together     = ('name', 'section')
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.section.name} - {self.name}"


# -----------------------------
# PRODUCT
# -----------------------------
class Product(models.Model):
    name     = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    buy_date = models.DateField(default=date.today)

    # ✅ Fix 4: default changed from 3 → 2
    low_stock_threshold = models.PositiveIntegerField(default=2)

    class Meta:
        # ✅ Fix 2: prevent duplicate products with same name+category
        unique_together = ('name', 'category')

    def __str__(self):
        return self.name


# -----------------------------
# PRICING (Size-based — ForeignKey)
# ✅ Fix 1: Changed OneToOneField → ForeignKey so each size has its own price
# ✅ Fix 3: Removed selling_price from here — it belongs in Sale only
# -----------------------------
class Pricing(models.Model):
    product       = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='pricings'
    )
    size          = models.CharField(max_length=10)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2)
    marked_price  = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Leave blank to auto-calculate (purchase rate × 1.5)"
    )

    class Meta:
        verbose_name_plural = "Pricings"

    def clean(self):
        # Auto-calculate marked price if empty
        if not self.marked_price:
            self.marked_price = self.purchase_rate * Decimal("1.50")

    def margin_percent(self):
        if self.marked_price and self.purchase_rate:
            return round(
                ((self.marked_price - self.purchase_rate) / self.purchase_rate) * 100,
                2
            )
        return 0

    def __str__(self):
        return f"{self.product.name} ({self.size}) — ₹{self.marked_price}"


# -----------------------------
# STOCK (Size-based)
# -----------------------------
class Stock(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    size     = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()

    class Meta:
        pass  # ← No unique_together!

    def __str__(self):
        return f"{self.product.name} - {self.size}"


# -----------------------------
# SALES (Daily EOD Records)
# ✅ Selling price stays here — entered at time of sale
# -----------------------------
class Sale(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    size     = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()

    purchase_rate_snapshot = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    marked_price_snapshot  = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # ✅ Selling price only entered during EOD sale recording
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount      = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    profit    = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # ✅ Fix 1: editable — user can enter past dates
    sold_date = models.DateField(
        default=None, null=True, blank=True,
        help_text="Leave blank to use today's date"
    )
    # ✅ Payment mode
    PAYMENT_CHOICES = [
        ('cash',     'Cash'),
        ('phonepay', 'PhonePe'),
        ('due',      'Due (Pay Later)'),
    ]
    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='cash'
    )
    is_due = models.BooleanField(default=False)
    due_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0.00, null=True, blank=True,
        help_text="Amount pending if payment is Due"
    )
    customer_name = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="Customer name (required for Due sales)"
    )
    customer_phone = models.CharField(
        max_length=15, null=True, blank=True,
        help_text="Customer phone (required for Due sales)"
    )
    # ✅ pricing_id — to handle multiple pricings for same product+size
    pricing_id = models.IntegerField(null=True, blank=True)
    remarks    = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Optional: e.g. Bhagwa, Red Pattern (shown as PRODUCT - Remarks)'
    )

    def clean(self):
        # Fetch size-specific pricing using pricing_id if available
        if self.pricing_id:
            pricing = Pricing.objects.filter(id=self.pricing_id).first()
        else:
            pricing = Pricing.objects.filter(product=self.product, size=self.size).first()
        if not pricing:
            raise ValidationError(
                f"No pricing found for {self.product.name} in size {self.size}."
            )

        purchase_rate = pricing.purchase_rate

        # Stock validation
        stock = Stock.objects.filter(product=self.product, size=self.size).first()
        if not stock:
            raise ValidationError(
                "Stock entry does not exist for this size."
            )
        total_stock = Stock.objects.filter(
            product=self.product, size=self.size
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        if self.quantity > total_stock:
            raise ValidationError(
                f"Not enough stock. Available: {total_stock}"
            )

        # Margin warning (20% minimum) — soft warning, not a block
        min_allowed = purchase_rate * Decimal("1.20")
        actual_margin = round((self.selling_price - purchase_rate) / purchase_rate * 100, 1)
        if self.selling_price < min_allowed:
            import warnings
            warnings.warn(
                f"Selling price ₹{self.selling_price} is below 20% margin. "
                f"Actual margin: {actual_margin}%. Minimum recommended: ₹{min_allowed:.2f}"
            )

        # Due payment validation
        if self.payment_mode == 'due':
            self.is_due = True
            self.due_amount = self.selling_price * self.quantity
            if not self.customer_name or not self.customer_phone:
                raise ValidationError(
                    "Customer name and phone are required for Due sales."
                )
        else:
            self.is_due = False
            self.due_amount = 0

    def save(self, *args, **kwargs):
        # ✅ Fix 1: auto-set sold_date if not provided
        if not self.sold_date:
            from django.utils import timezone
            self.sold_date = timezone.now()

        # ✅ Use pricing_id if available to avoid MultipleObjectsReturned
        if self.pricing_id:
            pricing = Pricing.objects.filter(id=self.pricing_id).first()
        else:
            pricing = Pricing.objects.filter(product=self.product, size=self.size).first()

        if not pricing:
            return

        # Snapshot pricing at time of sale
        self.purchase_rate_snapshot = pricing.purchase_rate
        self.marked_price_snapshot  = pricing.marked_price

        # Calculate profit
        self.profit = (
            (self.selling_price - self.purchase_rate_snapshot - self.discount)
            * self.quantity
        )

        super().save(*args, **kwargs)

        # Deduct stock
        stock = Stock.objects.filter(product=self.product, size=self.size).first()
        if stock:
            stock.quantity -= self.quantity
            stock.save()

            # Low stock WhatsApp alert
            from .utils import send_whatsapp_alert
            if stock.quantity <= self.product.low_stock_threshold:
                message = f"""
⚠️ LOW STOCK ALERT

Product : {self.product.name}
Size    : {self.size}
Remaining: {stock.quantity}

Please restock soon.
"""
                send_whatsapp_alert(message)

    def __str__(self):
        name = self.product.name
        if self.remarks:
            name = f"{name} - {self.remarks}"
        return f"Sale — {name} ({self.size})"


# -----------------------------
# SYSTEM SETTINGS
# -----------------------------
class SystemSettings(models.Model):
    show_purchase_rate = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "System Settings"


# -----------------------------
# AUDIT LOG
# -----------------------------
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    ]

    user        = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name  = models.CharField(max_length=100)
    object_id   = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=300)
    changes     = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-timestamp']
        verbose_name        = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return (
            f"{self.timestamp:%d %b %Y %H:%M} | "
            f"{self.user} | {self.action} | {self.model_name}"
        )