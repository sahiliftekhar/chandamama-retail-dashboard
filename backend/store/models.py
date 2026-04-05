from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date


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
        unique_together  = ('name', 'section')
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
        unique_together = ('product', 'size')
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
        unique_together = ('product', 'size')

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
    sold_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Fetch size-specific pricing
        try:
            pricing = Pricing.objects.get(product=self.product, size=self.size)
        except Pricing.DoesNotExist:
            raise ValidationError(
                f"No pricing found for {self.product.name} in size {self.size}."
            )

        purchase_rate = pricing.purchase_rate

        # Stock validation
        try:
            stock = Stock.objects.get(product=self.product, size=self.size)
        except Stock.DoesNotExist:
            raise ValidationError(
                "Stock entry does not exist for this size."
            )

        if self.quantity > stock.quantity:
            raise ValidationError(
                f"Not enough stock. Available: {stock.quantity}"
            )

        # Margin validation (20% minimum)
        min_allowed = purchase_rate * Decimal("1.20")
        if self.selling_price < min_allowed:
            raise ValidationError(
                f"Selling price ₹{self.selling_price} is below 20% margin. "
                f"Minimum allowed: ₹{min_allowed:.2f}"
            )

    def save(self, *args, **kwargs):
        pricing = Pricing.objects.get(product=self.product, size=self.size)

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
        stock = Stock.objects.get(product=self.product, size=self.size)
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
        return f"Sale — {self.product.name} ({self.size})"


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